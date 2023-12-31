#!/usr/bin/env python

# Python 2/3 compatibility imports
from __future__ import print_function
from six.moves import input
import speech_recognition as sr
from gtts import gTTS
import sys
import copy
import rospy
import moveit_commander
import moveit_msgs.msg
import geometry_msgs.msg

try:
    from math import pi, tau, dist, fabs, cos
except:  # For Python 2 compatibility
    from math import pi, fabs, cos, sqrt

    tau = 2.0 * pi


    def dist(p, q):
        return sqrt(sum((p_i - q_i) ** 2.0 for p_i, q_i in zip(p, q)))

from std_msgs.msg import String
from moveit_commander.conversions import pose_to_list


## END_SUB_TUTORIAL


def all_close(goal, actual, tolerance):
    """
    Convenience method for testing if the values in two lists are within a tolerance of each other.
    For Pose and PoseStamped inputs, the angle between the two quaternions is compared (the angle
    between the identical orientations q and -q is calculated correctly).
    @param: goal       A list of floats, a Pose or a PoseStamped
    @param: actual     A list of floats, a Pose or a PoseStamped
    @param: tolerance  A float
    @returns: bool
    """
    if type(goal) is list:
        for index in range(len(goal)):
            if abs(actual[index] - goal[index]) > tolerance:
                return False

    elif type(goal) is geometry_msgs.msg.PoseStamped:
        return all_close(goal.pose, actual.pose, tolerance)

    elif type(goal) is geometry_msgs.msg.Pose:
        x0, y0, z0, qx0, qy0, qz0, qw0 = pose_to_list(actual)
        x1, y1, z1, qx1, qy1, qz1, qw1 = pose_to_list(goal)
        # Euclidean distance
        d = dist((x1, y1, z1), (x0, y0, z0))
        # phi = angle between orientations
        cos_phi_half = fabs(qx0 * qx1 + qy0 * qy1 + qz0 * qz1 + qw0 * qw1)
        return d <= tolerance and cos_phi_half >= cos(tolerance / 2.0)

    return True


class MoveGroupPythonInterfaceTutorial(object):
    """MoveGroupPythonInterfaceTutorial"""

    def __init__(self):
        super(MoveGroupPythonInterfaceTutorial, self).__init__()

        ## First initialize `moveit_commander`_ and a `rospy`_ node:
        moveit_commander.roscpp_initialize(sys.argv)
        rospy.init_node("move_group_python_interface_tutorial", anonymous=True)

        ## Instantiate a `RobotCommander`_ object. Provides information such as the robot's
        ## kinematic model and the robot's current joint states
        robot = moveit_commander.RobotCommander()

        ## Instantiate a `PlanningSceneInterface`_ object.  This provides a remote interface
        ## for getting, setting, and updating the robot's internal understanding of the
        ## surrounding world:
        scene = moveit_commander.PlanningSceneInterface()

        ## Instantiate a `MoveGroupCommander`_ object.  This object is an interface
        ## to a planning group (group of joints).  In this tutorial the group is the primary
        ## arm joints in the Panda robot, so we set the group's name to "panda_arm".
        ## If you are using a different robot, change this value to the name of your robot
        ## arm planning group.
        ## This interface can be used to plan and execute motions:
        group_name = "panda_arm"
        move_group = moveit_commander.MoveGroupCommander(group_name)

        ## Create a `DisplayTrajectory`_ ROS publisher which is used to display
        ## trajectories in Rviz:
        display_trajectory_publisher = rospy.Publisher(
            "/move_group/display_planned_path",
            moveit_msgs.msg.DisplayTrajectory,
            queue_size=20,
        )

        ## END_SUB_TUTORIAL

        ## BEGIN_SUB_TUTORIAL basic_info
        ##
        ## Getting Basic Information
        ## ^^^^^^^^^^^^^^^^^^^^^^^^^
        # We can get the name of the reference frame for this robot:
        planning_frame = move_group.get_planning_frame()
        print("============ Planning frame: %s" % planning_frame)

        # We can also print the name of the end-effector link for this group:
        eef_link = move_group.get_end_effector_link()
        print("============ End effector link: %s" % eef_link)

        # We can get a list of all the groups in the robot:
        group_names = robot.get_group_names()
        print("============ Available Planning Groups:", robot.get_group_names())

        # Sometimes for debugging it is useful to print the entire state of the
        # robot:
        print("============ Printing robot state")
        print(robot.get_current_state())
        print("")
        ## END_SUB_TUTORIAL

        # Misc variables
        self.box_name = ""
        self.box_loc = geometry_msgs.msg.PoseStamped()
        self.robot = robot
        self.scene = scene
        self.move_group = move_group
        self.display_trajectory_publisher = display_trajectory_publisher
        self.planning_frame = planning_frame
        self.eef_link = eef_link
        self.group_names = group_names
        self.goal = geometry_msgs.msg.Pose()

    def go_to_joint_state(self):
        # Copy class variables to local variables to make the web tutorials more clear.
        # In practice, you should use the class variables directly unless you have a good
        # reason not to.
        move_group = self.move_group

        ## BEGIN_SUB_TUTORIAL plan_to_joint_state
        ##
        ## Planning to a Joint Goal
        ## ^^^^^^^^^^^^^^^^^^^^^^^^
        ## The Panda's zero configuration is at a `singularity <https://www.quora.com/Robotics-What-is-meant-by-kinematic-singularity>`_, so the first
        ## thing we want to do is move it to a slightly better configuration.
        ## We use the constant `tau = 2*pi <https://en.wikipedia.org/wiki/Turn_(angle)#Tau_proposals>`_ for convenience:
        # We get the joint values from the group and change some of the values:
        joint_goal = move_group.get_current_joint_values()
        joint_goal[0] = 0
        joint_goal[1] = 0
        joint_goal[2] = 0
        joint_goal[3] = -1.57
        joint_goal[4] = 0
        joint_goal[5] = 1.57
        joint_goal[6] = 0.785

        # The go command can be called with joint values, poses, or without any
        # parameters if you have already set the pose or joint target for the group
        move_group.go(joint_goal, wait=True)

        # Calling ``stop()`` ensures that there is no residual movement
        move_group.stop()

        ## END_SUB_TUTORIAL

        # For testing:
        current_joints = move_group.get_current_joint_values()
        return all_close(joint_goal, current_joints, 0.01)

    def go_to_pose_goal(self):
        # Copy class variables to local variables to make the web tutorials more clear.
        # In practice, you should use the class variables directly unless you have a good
        # reason not to.
        move_group = self.move_group

        ## BEGIN_SUB_TUTORIAL plan_to_pose
        ##
        ## Planning to a Pose Goal
        ## ^^^^^^^^^^^^^^^^^^^^^^^
        ## We can plan a motion for this group to a desired pose for the
        ## end-effector:
        pose_goal = self.goal

        move_group.set_pose_target(pose_goal)
        ## Now, we call the planner to compute the plan and execute it.
        # `go()` returns a boolean indicating whether the planning and execution was successful.
        success = move_group.go(wait=True)
        # Calling `stop()` ensures that there is no residual movement
        move_group.stop()
        # It is always good to clear your targets after planning with poses.
        # Note: there is no equivalent function for clear_joint_value_targets().
        move_group.clear_pose_targets()

        ## END_SUB_TUTORIAL

        # For testing:
        # Note that since this section of code will not be included in the tutorials
        # we use the class variable rather than the copied state variable
        current_pose = self.move_group.get_current_pose().pose
        return all_close(pose_goal, current_pose, 0.01)

    def wait_for_state_update(
            self, box_is_known=False, box_is_attached=False, timeout=4
    ):
        # Copy class variables to local variables to make the web tutorials more clear.
        # In practice, you should use the class variables directly unless you have a good
        # reason not to.
        box_name = self.box_name
        scene = self.scene

        ## BEGIN_SUB_TUTORIAL wait_for_scene_update
        ##
        ## Ensuring Collision Updates Are Received
        ## ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        ## If the Python node was just created (https://github.com/ros/ros_comm/issues/176),
        ## or dies before actually publishing the scene update message, the message
        ## could get lost and the box will not appear. To ensure that the updates are
        ## made, we wait until we see the changes reflected in the
        ## ``get_attached_objects()`` and ``get_known_object_names()`` lists.
        ## For the purpose of this tutorial, we call this function after adding,
        ## removing, attaching or detaching an object in the planning scene. We then wait
        ## until the updates have been made or ``timeout`` seconds have passed.
        ## To avoid waiting for scene updates like this at all, initialize the
        ## planning scene interface with  ``synchronous = True``.
        start = rospy.get_time()
        seconds = rospy.get_time()
        while (seconds - start < timeout) and not rospy.is_shutdown():
            # Test if the box is in attached objects
            attached_objects = scene.get_attached_objects([box_name])
            is_attached = len(attached_objects.keys()) > 0

            # Test if the box is in the scene.
            # Note that attaching the box will remove it from known_objects
            is_known = box_name in scene.get_known_object_names()

            # Test if we are in the expected state
            if (box_is_attached == is_attached) and (box_is_known == is_known):
                return True

            # Sleep so that we give other threads time on the processor
            rospy.sleep(0.1)
            seconds = rospy.get_time()

        # If we exited the while loop without returning then we timed out
        return False
        ## END_SUB_TUTORIAL

    def attach_box(self, timeout=4):
        # Copy class variables to local variables to make the web tutorials more clear.
        # In practice, you should use the class variables directly unless you have a good
        # reason not to.
        box_name = self.box_name
        robot = self.robot
        scene = self.scene
        eef_link = self.eef_link
        group_names = self.group_names

        ## BEGIN_SUB_TUTORIAL attach_object
        ##
        ## Attaching Objects to the Robot
        ## ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        ## Next, we will attach the box to the Panda wrist. Manipulating objects requires the
        ## robot be able to touch them without the planning scene reporting the contact as a
        ## collision. By adding link names to the ``touch_links`` array, we are telling the
        ## planning scene to ignore collisions between those links and the box. For the Panda
        ## robot, we set ``grasping_group = 'hand'``. If you are using a different robot,
        ## you should change this value to the name of your end effector group name.
        grasping_group = "panda_hand"
        touch_links = robot.get_link_names(group=grasping_group)
        scene.attach_box(eef_link, box_name, touch_links=touch_links)
        ## END_SUB_TUTORIAL

        # We wait for the planning scene to update.
        return self.wait_for_state_update(
            box_is_attached=True, box_is_known=False, timeout=timeout
        )

    def detach_box(self, timeout=4):
        # Copy class variables to local variables to make the web tutorials more clear.
        # In practice, you should use the class variables directly unless you have a good
        # reason not to.
        box_name = self.box_name
        scene = self.scene
        eef_link = self.eef_link

        ## BEGIN_SUB_TUTORIAL detach_object
        ##
        ## Detaching Objects from the Robot
        ## ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        ## We can also detach and remove the object from the planning scene:
        scene.remove_attached_object(eef_link, name=box_name)
        ## END_SUB_TUTORIAL

        # We wait for the planning scene to update.
        return self.wait_for_state_update(
            box_is_known=True, box_is_attached=False, timeout=timeout
        )

    def remove_box(self, timeout=4):
        # Copy class variables to local variables to make the web tutorials more clear.
        # In practice, you should use the class variables directly unless you have a good
        # reason not to.
        box_name = self.box_name
        scene = self.scene

        ## BEGIN_SUB_TUTORIAL remove_object
        ##
        ## Removing Objects from the Planning Scene
        ## ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        ## We can remove the box from the world.
        scene.remove_world_object(box_name)

        ## **Note:** The object must be detached before we can remove it from the world
        ## END_SUB_TUTORIAL

        # We wait for the planning scene to update.
        return self.wait_for_state_update(
            box_is_attached=False, box_is_known=False, timeout=timeout
        )


def main():
    try:
        # Box Codes
        red_counter = 1
        blue_counter = 1
        green_counter = 1
        # Preset positions for the robot
        presets = {
            "home": [0.5, 0, 0.5],
            "b_bin": [0, 0.5, 0.3],
            "g_bin": [-0.5, 0, 0.3],
            "r_bin": [0, -0.5, 0.3],
        }

        red_boxes = {
            1: ["R1", [0.4, 0.3, 0.4]],
            2: ["R2", [0.6, 0, 0.4]],
        }

        green_boxes = {
            1: ["G1", [0.4, 0, 0.4]],
            2: ["G2", [0.6, -0.3, 0.4]],
        }

        blue_boxes = {
            1: ["B1", [0.4, -0.3, 0.4]],
            2: ["B2", [0.6, 0.3, 0.4]],
        }

        tutorial = MoveGroupPythonInterfaceTutorial()

        # NOTE: this example requires PyAudio because it uses the Microphone class
        # from playsound import playsound
        # from __future__ import print_function
        # from six.moves import input

        # import sys
        # import copy
        # import rospy
        # import moveit_commander
        ##import moveit_msgs.msg
        # import geometry_msgs.msg
        # from std_msgs.msg import String
        # from moveit_commander.conversions import pose_to_list
        text = 'Say something!'
        language = 'en'
        obj = gTTS(text=text, lang=language, slow=False)
        obj.save("welcome.mp3")
        # obtain audio from the microphone
        r = sr.Recognizer()
        with sr.Microphone() as source:
            # playsound("welcome.mp3")
            print("Say something!")
            audio = r.listen(source)

        # recognize speech using Sphinx
        # try:
        #    print("Sphinx thinks you said " + r.recognize_sphinx(audio))
        # except sr.UnknownValueError:
        #    print("Sphinx could not understand audio")
        # except sr.RequestError as e:
        #    print("Sphinx error; {0}".format(e))
        class Queue:
            "A container with a first-in-first-out (FIFO) queuing policy."

            def __init__(self):
                self.list = []

            def push(self, item):
                "Enqueue the 'item' into the queue"
                self.list.insert(0, item)

            def pop(self):
                """
                  Dequeue the earliest enqueued item still in the queue. This
                  operation removes the item from the queue.
                """
                return self.list.pop()

            def isEmpty(self):
                "Returns true if the queue is empty"
                return len(self.list) == 0

        # recognize speech using Google Speech Recognition
        try:
            # for testing purposes, we're just using the default API key
            # to use another API key, use `r.recognize_google(audio, key="GOOGLE_SPEECH_RECOGNITION_API_KEY")`
            # instead of `r.recognize_google(audio)`
            print("Google Speech Recognition thinks you said " + r.recognize_google(audio))
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio")
        except sr.RequestError as e:
            print("Could not request results from Google Speech Recognition service; {0}".format(e))

        audio = r.recognize_google(audio)
        print(audio)
        color = ["red", "green", 'blue']
        command = ["pick", "place"]
        c_count = [0, 0, 0]
        com_count = [0, 0]
        audio = audio.split()
        c_queue = Queue()
        com_queue = Queue()
        for i in audio:
            for j in range(len(color)):
                if i == color[j]:
                    c_count[j] = c_count[j] + 1
                    c_queue.push(i)
            for j in range(len(command)):
                if i == command[j]:
                    com_count[j] = com_count[j] + 1
                    com_queue.push(i)

        while(com_queue):
            if com_queue[0]== "pick":
                if c_queue[0]== "red":
                    box_position = red_boxes.pop(red_counter)
                    red_counter += 1
                    print(f"The position of {box_name} box is {box_position[1]} and the name is {box_position[0]}")
                    c_queue.pop()
                elif c_queue[0] == "green":
                    box_position = green_boxes.pop(green_counter)
                    green_counter += 1
                    print(f"The position of {box_name} box is {box_position} and the name is {box_position[0]}")
                    c_queue.pop()
                elif c_queue[0]== "blue":
                    box_position = blue_boxes.pop(blue_counter)
                    blue_counter += 1
                    print(f"The position of {box_name} box is {box_position} and the name is {box_position[0]}")
                    c_queue.pop()
                else:
                    print("Invalid box name")

                tutorial.goal.orientation.x = -1
                tutorial.goal.position.x = box_position[1][0]
                tutorial.goal.position.y = box_position[1][1]
                tutorial.goal.position.z = box_position[1][2]
                tutorial.box_name = box_position[0]
                tutorial.go_to_pose_goal()
                tutorial.attach_box()
            elif com_queue[0] == "place":
                if c_queue[0] == "blue":
                    tutorial.goal.orientation.x = -1
                    tutorial.goal.position.x = presets["b_bin"][0]
                    tutorial.goal.position.y = presets["b_bin"][1]
                    tutorial.goal.position.z = presets["b_bin"][2]
                    c_queue.pop()
                elif c_queue[0] == "green":
                    tutorial.goal.orientation.x = -1
                    tutorial.goal.position.x = presets["g_bin"][0]
                    tutorial.goal.position.y = presets["g_bin"][1]
                    tutorial.goal.position.z = presets["g_bin"][2]
                    c_queue.pop()
                elif c_queue[0] == "red":
                    tutorial.goal.orientation.x = -1
                    tutorial.goal.position.x = presets["r_bin"][0]
                    tutorial.goal.position.y = presets["r_bin"][1]
                    tutorial.goal.position.z = presets["r_bin"][2]
                    c_queue.pop()
                else:
                    print("Invalid bin name")
                tutorial.go_to_pose_goal()

                tutorial.detach_box()
                tutorial.remove_box()
                com_queue.pop()
                tutorial.go_to_joint_state()

                if red_counter == 2 and green_counter == 2 and blue_counter == 2:
                    break
        # recognize speech using Google Cloud Speech
        # GOOGLE_CLOUD_SPEECH_CREDENTIALS = r"""INSERT THE CONTENTS OF THE GOOGLE CLOUD SPEECH JSON CREDENTIALS FILE HERE"""
        # try:
        #    print("Google Cloud Speech thinks you said " + r.recognize_google_cloud(audio, credentials_json=GOOGLE_CLOUD_SPEECH_CREDENTIALS))
        # except sr.UnknownValueError:
        #    print("Google Cloud Speech could not understand audio")
        # except sr.RequestError as e:
        #    print("Could not request results from Google Cloud Speech service; {0}".format(e))

        # recognize speech using Wit.ai
        # WIT_AI_KEY = "INSERT WIT.AI API KEY HERE"  # Wit.ai keys are 32-character uppercase alphanumeric strings
        # try:
        #    print("Wit.ai thinks you said " + r.recognize_wit(audio, key=WIT_AI_KEY))
        # except sr.UnknownValueError:
        #    print("Wit.ai could not understand audio")
        # except sr.RequestError as e:
        #    print("Could not request results from Wit.ai service; {0}".format(e))

        # recognize speech using Microsoft Bing Voice Recognition
        # BING_KEY = "INSERT BING API KEY HERE"  # Microsoft Bing Voice Recognition API keys 32-character lowercase hexadecimal strings
        # try:
        #    print("Microsoft Bing Voice Recognition thinks you said " + r.recognize_bing(audio, key=BING_KEY))
        # except sr.UnknownValueError:
        #    print("Microsoft Bing Voice Recognition could not understand audio")
        # except sr.RequestError as e:
        #    print("Could not request results from Microsoft Bing Voice Recognition service; {0}".format(e))

        # recognize speech using Microsoft Azure Speech
        # AZURE_SPEECH_KEY = "INSERT AZURE SPEECH API KEY HERE"  # Microsoft Speech API keys 32-character lowercase hexadecimal strings
        # try:
        #    print("Microsoft Azure Speech thinks you said " + r.recognize_azure(audio, key=AZURE_SPEECH_KEY))
        # except sr.UnknownValueError:
        #    print("Microsoft Azure Speech could not understand audio")
        # except sr.RequestError as e:
        #    print("Could not request results from Microsoft Azure Speech service; {0}".format(e))

        # recognize speech using Houndify
        # HOUNDIFY_CLIENT_ID = "INSERT HOUNDIFY CLIENT ID HERE"  # Houndify client IDs are Base64-encoded strings
        # HOUNDIFY_CLIENT_KEY = "INSERT HOUNDIFY CLIENT KEY HERE"  # Houndify client keys are Base64-encoded strings
        # try:
        #    print("Houndify thinks you said " + r.recognize_houndify(audio, client_id=HOUNDIFY_CLIENT_ID, client_key=HOUNDIFY_CLIENT_KEY))
        # except sr.UnknownValueError:
        #    print("Houndify could not understand audio")
        # except sr.RequestError as e:
        #    print("Could not request results from Houndify service; {0}".format(e))

        # recognize speech using IBM Speech to Text
        # IBM_USERNAME = "INSERT IBM SPEECH TO TEXT USERNAME HERE"  # IBM Speech to Text usernames are strings of the form XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
        # IBM_PASSWORD = "INSERT IBM SPEECH TO TEXT PASSWORD HERE"  # IBM Speech to Text passwords are mixed-case alphanumeric strings
        # try:
        #    print("IBM Speech to Text thinks you said " + r.recognize_ibm(audio, username=IBM_USERNAME, password=IBM_PASSWORD))
        # except sr.UnknownValueError:
        #    print("IBM Speech to Text could not understand audio")
        # except sr.RequestError as e:
        #    print("Could not request results from IBM Speech to Text service; {0}".format(e))

        # recognize speech using whisper
        # try:
        #    print("Whisper thinks you said " + r.recognize_whisper(audio, language="english"))
        # except sr.UnknownValueError:
        #    print("Whisper could not understand audio")
        # except sr.RequestError as e:
        #    print("Could not request results from Whisper")

        # recognize speech using Whisper API
        # OPENAI_API_KEY = "INSERT OPENAI API KEY HERE"
        # try:
        #    print(f"Whisper API thinks you said {r.recognize_whisper_api(audio, api_key=OPENAI_API_KEY)}")
        # except sr.RequestError as e:
        #    print("Could not request results from Whisper API")

        print("You have completed the task!")

    except rospy.ROSInterruptException:
        return
    except KeyboardInterrupt:
        return


if __name__ == "__main__":
    main()
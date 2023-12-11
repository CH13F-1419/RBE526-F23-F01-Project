# RBE526-F23-F01-Project
Codebase for the semester project submission for RBE 526, Human Robot Interaction, in Fall 2023. See each branch for its corresponding code (main - KBM, vr - VR, patch - VO).

## Running the KBM packages
- Using ROS Noetic on Ubuntu 20.04
- Catkin build the package
- run `roslaunch frankapanda_moveit_config demo.launch`
- Load `scene1.rviz` from the same package's scene files for RViz
- run `rosrun moveit_tutorials move_group_interface_tutorial.py`
- Use the commands to run the program
- Alternatively, use the RViz GUI itself to manipulate the robot

## Running the VR packages
- Unity -> import the project
- Connect the headset via USB C cable
- Choose the connected device in File > Build > Settings
- Connect to ROS 1 using TCP endpoints in settings
- Build And Run (Ctrl-B)

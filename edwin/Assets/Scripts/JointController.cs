using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Unity.Robotics.UrdfImporter;

namespace Unity.Robotics.UrdfImporter.Control
{
public class JointController : MonoBehaviour
{
    Unity.Robotics.UrdfImporter.Control.PandaController controller;

    public Unity.Robotics.UrdfImporter.Control.RotationDirection direction;
    public float speed ;
    public float torque ;
    public float acceleration;
    public ArticulationBody joint;


    void Start()
    {
        direction = 0;
        controller = (Unity.Robotics.UrdfImporter.Control.PandaController)this.GetComponentInParent(typeof(Unity.Robotics.UrdfImporter.Control.PandaController));
        joint = this.GetComponent<ArticulationBody>();
        controller.UpdateControlType(this);
        speed = controller.speed;
        torque = controller.torque;
        acceleration = controller.acceleration;
    }

    void FixedUpdate(){

        speed = controller.speed;
        torque = controller.torque;
        acceleration = controller.acceleration;


        if (joint.jointType != ArticulationJointType.FixedJoint)
        {
          
                ArticulationDrive currentDrive = joint.xDrive;
                float newTargetDelta = (int)direction * Time.fixedDeltaTime * speed;

                if (joint.jointType == ArticulationJointType.RevoluteJoint)
                {
                    if (joint.twistLock == ArticulationDofLock.LimitedMotion)
                    {
                        if (newTargetDelta + currentDrive.target > currentDrive.upperLimit)
                        {
                            currentDrive.target = currentDrive.upperLimit;
                        }
                        else if (newTargetDelta + currentDrive.target < currentDrive.lowerLimit)
                        {
                            currentDrive.target = currentDrive.lowerLimit;
                        }
                        else
                        {
                            currentDrive.target += newTargetDelta;
                        }
                    }
                    else
                    {
                        currentDrive.target += newTargetDelta;
   
                    }
                }

                // else if (joint.jointType == ArticulationJointType.PrismaticJoint)
                // {
                //     if (joint.linearLockX == ArticulationDofLock.LimitedMotion)
                //     {
                //         if (newTargetDelta + currentDrive.target > currentDrive.upperLimit)
                //         {
                //             currentDrive.target = currentDrive.upperLimit;
                //         }
                //         else if (newTargetDelta + currentDrive.target < currentDrive.lowerLimit)
                //         {
                //             currentDrive.target = currentDrive.lowerLimit;
                //         }
                //         else
                //         {
                //             currentDrive.target += newTargetDelta;
                //         }
                //     }
                //     else
                //     {
                //         currentDrive.target += newTargetDelta;
   
                //     }
                // }

                joint.xDrive = currentDrive;

        }
    }
}
}
#include "Robot.h"

namespace MyRobot
{
  Robot::Robot()
  : nMotors(0)
  {
    
  }

  Robot::~Robot()
  {
  }

  void Robot::attachMotor2Robot(Motor* pMotor)
  {
    if (nMotors >= MAX_MOTORS)
    {
      return;
    }

    for (int i = 0; i < nMotors; i++)
    {
      Motor* p = motors_[i];
      if (p == NULL)
      {
        continue;
      }

      if (p->getPartType() == pMotor->getPartType())
      {
        return;
      }
    }

    motors_[nMotors++] = pMotor;
  }

  Motor* Robot::getMotor(PARTTYPE type)
  {
    Motor* pRet = NULL;

    if (nMotors == 0)
    {
      return NULL;
    }

    for (int i = 0; i < nMotors; i++)
    {
      Motor* pMotor = motors_[i];
      if (pMotor == NULL)
      {
        continue;
      }

      if (pMotor->getPartType() == type)
      {
        pRet = pMotor;
        return pRet;
      }
    }

    return pRet;
  }

  void Robot::initialize()
  {
    for (int i = 0; i < nMotors; i++)
    {
      Motor* pMotor = motors_[i];
      if (pMotor != NULL)
      {
        pMotor->initialize();
      }
    }
  }
}
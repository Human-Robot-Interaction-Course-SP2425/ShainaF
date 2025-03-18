#ifndef __ROBOT_H__
#define __ROBOT_H__

#include <stdint.h>
#include "Motor.h"


namespace MyRobot
{
  const uint8_t MAX_MOTORS = 4;
  class Robot
  {
  public:
    Robot();
    ~Robot();

    void initialize();

    void attachMotor2Robot(Motor* pMotor);
    Motor* getMotor(PARTTYPE type);

  public:

  private:
    Motor* motors_[MAX_MOTORS];
    uint8_t nMotors;
  };
}

#endif    //__ROBOT_H__
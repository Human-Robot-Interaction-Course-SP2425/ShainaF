#include "Motor.h" 

namespace MyRobot
{
  float normalizeAngle(float angle)
  {
    while (angle < 0) angle += 360;
    while (angle >= 360) angle -= 360;

    return angle;
  }

    Motor::Motor(PARTTYPE type, float reset_pos, float range_pos_low, float range_pos_high, MotorImpl& impl)
    : type_(type), reset_pos_(reset_pos), range_pos_low_(range_pos_low), range_pos_high_(range_pos_high), impl_(impl)
    {

    }

    Motor::~Motor()
    {

    }

    void Motor::initialize()
    {
      impl_.switchTorque(false);
      impl_.setWorkingMode();
      impl_.switchTorque(true);
    }

    float Motor::getAngle()
    {
      return impl_.getAngle();
    }

    void Motor::moveAngle(float angle, int32_t speed, int32_t acc)
    {
      float targetAngle = angle;
      float curAngle = impl_.getAngle();
      targetAngle = normalizeAngle(angle);
      curAngle = normalizeAngle(curAngle);

      float directDiff = abs(curAngle - targetAngle);
      float corssZeroDiff = 360 - max(curAngle, targetAngle) + min(curAngle, targetAngle);
      float smallestDiff = min(directDiff, corssZeroDiff);

      if (smallestDiff <= 0.5)
      {
        //Here we don't want the motor to turn a whole round to reach the same angle
        //Because it would twist the joint of the robot.
        return;
      }

      impl_.moveAngle(angle, speed, acc);
    }
}
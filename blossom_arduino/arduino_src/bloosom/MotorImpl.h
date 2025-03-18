#ifndef __MOTORIMPL_H__
#define __MOTORIMPL_H__

#include <stdint.h>
#include <DynamixelShield.h>


namespace MyRobot
{
  class MotorImpl
  {
  public:
    MotorImpl(uint8_t id, DynamixelShield& dxl);
    ~MotorImpl();

    void move(int32_t pos, int32_t speed = -1, int32_t acc = -1);
    void moveAngle(float angle, int32_t speed = -1, int32_t acc = -1);
    void calibrate();
    void resetCalibration();
    int32_t getPos();
    float getAngle();
    int32_t getSpeed();
    void switchTorque(bool on = true);
    void setWorkingMode();
    void setId(uint8_t id) { id_ = id; }

  private:
    uint8_t id_;
    int32_t pos_;
    int32_t pos_offset_;
    int32_t speed_;
    int32_t def_speed_;
    float angle_;

    DynamixelShield& dxl_;
  };
}


#endif.   //__MOTOR_H__
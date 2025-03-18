#include "MotorImpl.h"

namespace MyRobot
{
    MotorImpl::MotorImpl(uint8_t id, DynamixelShield& dxl)
      : id_(id),
        dxl_(dxl),
        pos_(0),
        pos_offset_(0),
        speed_(0),
        def_speed_(100)
    {
      this->pos_ = getPos();
      this->speed_ = getSpeed();
      this->angle_ = getAngle();
    }

    MotorImpl::~MotorImpl()
    {

    }

    void MotorImpl::move(int32_t pos, int32_t speed, int32_t acc)
    {
      this->pos_ = pos;

      if (speed != -1)
      {
        dxl_.setGoalSpeed(this->id_, speed);
      }
      else
      {
        dxl_.setGoalSpeed(this->id_, this->def_speed_);
      }

      dxl_.setGoalPosition(this->id_, this->pos_ + this->pos_offset_);
    }

    void MotorImpl::moveAngle(float angle, int32_t speed, int32_t acc)
    {
      this->angle_ = angle;

      if (speed != -1)
      {
        dxl_.setGoalSpeed(this->id_, speed);
      }
      else
      {
        dxl_.setGoalSpeed(this->id_, this->def_speed_);
      }

      dxl_.setGoalPosition(this->id_, this->angle_, UNIT_DEGREE);

    }

    void MotorImpl::calibrate()
    {
      this->pos_offset_ = this->pos_;
      this->pos_ = 0;
    }

    void MotorImpl::resetCalibration()
    {
      this->pos_offset_ = 0;
      move(0);
      this->pos_ = dxl_.getCurPosition(this->id_);
    }

    int32_t MotorImpl::getPos()
    {
      return dxl_.getPresentPosition(this->id_);
    }

    float MotorImpl::getAngle()
    {
      return dxl_.getPresentPosition(this->id_, UNIT_DEGREE);
    }

    int32_t MotorImpl::getSpeed()
    {
      return dxl_.getCurSpeed(this->id_);
    }

    void MotorImpl::switchTorque(bool on)
    {
      if (on)
      {
        dxl_.torqueOn(this->id_);
      }
      else
      {
        dxl_.torqueOff(this->id_);
      }
    }

    void MotorImpl::setWorkingMode()
    {
      dxl_.setOperatingMode(this->id_, OP_POSITION);
    }

}
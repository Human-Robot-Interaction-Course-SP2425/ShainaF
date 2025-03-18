#ifndef __MOTOR_H__
#define __MOTOR_H__

#include <stdint.h>
#include "MotorImpl.h"

namespace MyRobot
{   
    typedef enum 
    {
        BASE = 0,
        TOWER_1 = 1,
        TOWER_2 = 2,
        TOWER_3 = 3,
        EAR = 4,
        MAX_PARTS_TYPES
    } PARTTYPE;
    class Motor
    {
    public:
        Motor(PARTTYPE type, float reset_pos, float range_pos_low, float range_pos_high, MotorImpl& impl);
        ~Motor();

        PARTTYPE getPartType() { return type_; }

        void initialize();

        void moveAngle(float angle, int32_t speed = -1, int32_t acc = -1);
        float getAngle();

        void setType(const PARTTYPE& type) { type_ = type; }
        PARTTYPE getType() { return type_; }

        float getResetPos() { return reset_pos_; };
        void setResetPos(float reset_pos) { reset_pos_ = reset_pos; }

        float getRangePosLow() { return range_pos_low_; }
        void setRangePosLow(float range_pos_low) { range_pos_low_ = range_pos_low; }

        float getRangePosHigh() { return range_pos_high_; }
        void setRangePosHigh(float range_pos_high) { range_pos_high_ = range_pos_high; }

    private:
        PARTTYPE type_;
        float reset_pos_;
        float range_pos_low_;
        float range_pos_high_;
        MotorImpl& impl_;
    };
}

#endif    //__MOTOR_H__
#ifndef __CONFIGS_H__
#define __CONFIGS_H__

#include <stdint.h>

namespace MyRobot
{  
  struct MotorConfig
  {
    uint8_t id;
    float reset_pos = 0;
    float range_pos[2] = {0, 0};
  };
}

#endif.   //__CONFIGS_H__
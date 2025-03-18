#ifndef __FRAME_H__
#define __FRAME_H__

#include "Motor.h"
#include <vector>

namespace MyRobot
{
    struct Position
    {
        PARTTYPE part_;
        float position_;
    };

    class Frame
    {
    public:
      friend class Sequence;
      Frame(float durationMs = 0.0);
      void addPosition(const Position& position);
      int size() { return positions_.size();}
      bool empty() { return positions_.empty();}
      float getDurationMs() const { return durationMs_; }
      std::vector<Position> getPositions() const { return positions_; }
      Frame& operator=(const Frame& other);
    private:
        std::vector<Position> positions_;
        float durationMs_;
    };
}


#endif    //__FRAME_H__
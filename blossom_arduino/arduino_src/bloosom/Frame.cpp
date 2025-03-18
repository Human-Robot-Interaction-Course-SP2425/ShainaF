#include "Frame.h"

namespace MyRobot
{
  Frame::Frame(float durationMs)
    : durationMs_(durationMs)
  {

  }
  
  void Frame::addPosition(const Position& position)
  {
    positions_.push_back(position);
  }

  Frame& Frame::operator=(const Frame& other)
  {
    if (this != &other)
    {
      this->durationMs_ = other.durationMs_;
      this->positions_ = other.positions_;
    }
  }
  
}
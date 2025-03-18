#include "Sequence.h"

namespace MyRobot
{
  Sequence::Sequence(const std::string& animation)
    : animation_(animation)
  {

  }

  void Sequence::appendList(const Frame& frame)
  {
    frameList_.push_back(frame);
  }

  Sequence& Sequence::operator=(const Sequence& other)
  {
    if (this != &other)
    {
      this->animation_ = other.animation_;
      this->frameList_ = other.frameList_;
    }

    return *this;
  }
}
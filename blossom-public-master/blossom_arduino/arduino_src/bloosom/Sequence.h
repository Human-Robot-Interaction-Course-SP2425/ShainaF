#ifndef __SEQUENCE_H__
#define __SEQUENCE_H__

#include <ArduinoJson.h>
#include "Frame.h"
#include <list>
#include <string>

namespace MyRobot
{
  class Sequence
  {
  public:
    friend class ConfigUtil;
    friend class SequencePlayer;
    Sequence(const std::string& animation = "Unknown");
    void appendList(const Frame& frame);
    Sequence& operator=(const Sequence& other);

    std::list<Frame> getFrameList() { return frameList_; }
  private:
    std::string animation_;
    std::list<Frame> frameList_;
  };
    
}

#endif    //__SEQUENCE_H__
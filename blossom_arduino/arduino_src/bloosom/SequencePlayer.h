#ifndef __SEQUENCEPLAYER_H__
#define __SEQUENCEPLAYER_H__

#include <functional>
#include <list>
#include "Robot.h"
#include "Sequence.h"

namespace MyRobot
{
  class SequencePlayer
  {
  public:
    typedef std::function<void(std::string&)> PRINTOUTFUNCTION;
    static SequencePlayer* getInstance();
    SequencePlayer(const SequencePlayer&) = delete;
    SequencePlayer& operator=(const SequencePlayer&) = delete;

    void loadSequence(const Sequence& sequence);
    void play(Robot& robot, PRINTOUTFUNCTION prtFunc, bool onRealMotor = false) const;
    
    std::list<float> getIntervalSeries() const { return delayIntervals_; }

  private:
    SequencePlayer();

    void PlayFrame(const Robot& robot, const Frame& frame) const;
  private:
    static SequencePlayer* instance_;
    Sequence sequence_;
    std::list<float> delayIntervals_;
  };
}

#endif  //__SEQUENCEPLAYER_H__
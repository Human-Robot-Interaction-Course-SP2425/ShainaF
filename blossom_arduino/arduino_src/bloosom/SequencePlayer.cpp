#include <sstream>
#include "SequencePlayer.h"

#include <Arduino.h>

namespace MyRobot
{
  SequencePlayer* SequencePlayer::instance_ = nullptr;

  SequencePlayer* SequencePlayer::getInstance()
  {
    if (nullptr == instance_)
    {
      instance_ = new SequencePlayer();
    }

    return instance_;
  }

  SequencePlayer::SequencePlayer()
  {

  }

  void SequencePlayer::loadSequence(const Sequence& sequence)
  {
    sequence_ = sequence;

    std::list<Frame>::const_iterator itr;

    if (sequence_.frameList_.empty())
    {
      //Empty frameList, do nothing.
      return;
    }

    delayIntervals_.clear();
    for (itr = sequence_.frameList_.begin(); itr != sequence_.frameList_.end(); itr++)
    {
      auto itr1 = itr;
      itr1++;
      
      if (itr1 == sequence_.frameList_.end())
      {
        break;
      }

      auto delay = itr1->getDurationMs() - itr->getDurationMs();
      if (delay < 0)
      {
        continue;
      }
      
      delayIntervals_.push_back(delay);
    }
  }

  void SequencePlayer::PlayFrame(const Robot& robot, const Frame& frame) const
  {

  }

  void SequencePlayer::play(Robot& robot, PRINTOUTFUNCTION prtFunc, bool onRealMotor) const
  {
    auto itr = sequence_.frameList_.begin();
    auto itr1 = delayIntervals_.begin();

    if (sequence_.frameList_.empty())
    {
      std::string logStr("Empty Sequence.");
      prtFunc(logStr);
      return;
    }
    else if (sequence_.frameList_.size() == 1)
    {
      auto pos = itr->getPositions();
      auto posItr = pos.begin();
      for (posItr; posItr != pos.end(); posItr++)
      {
        auto part = posItr->part_;
        auto position = posItr->position_;
        std::stringstream ss;
        std::string strLog;
        ss << "Command Part: " << part << " Move to Pos: " << position;
        strLog += ss.str();
        prtFunc(strLog);
        if (onRealMotor)
        {
          Motor* pMotor = robot.getMotor(part);
          if (pMotor == nullptr)
          {
            std::stringstream ss1;
            std::string strLog1;
            ss1 << "Failed to get Motor Instance (Type): " << part;
            strLog1 += ss1.str();

            prtFunc(strLog1);
            continue;
          }

          pMotor->moveAngle(position);
        }
      }
    }
    else
    {
      for (itr; itr != sequence_.frameList_.end(); itr++)
      {
        auto pos = itr->getPositions();
        auto posItr = pos.begin();
        for (posItr; posItr != pos.end(); posItr++)
        {
          auto part = posItr->part_;
          auto position = posItr->position_;
          std::stringstream ss;
          std::string strLog;
          ss << "Command Part: " << part << " Move to Pos: " << position;
          strLog += ss.str();
          if (onRealMotor)
          {
            Motor* pMotor = robot.getMotor(part);
            if (pMotor == nullptr)
            {
              std::stringstream ss1;
              std::string strLog1;
              ss1 << "Failed to get Motor Instance (Type): " << part;
              strLog1 += ss1.str();

              prtFunc(strLog1);
              continue;
            }

            pMotor->moveAngle(position);
          }
          prtFunc(strLog);
        }
        if (itr1 != delayIntervals_.end())
        {
          std::stringstream ss;
          std::string strLog;
          ss << "Delay: " << *itr1 << " ms";
          strLog += ss.str();
          prtFunc(strLog);
          delay(*itr1);
          itr1++;
        }
      }
    }
  }  
}
#ifndef __CONFIGUTIL_H__
#define __CONFIGUTIL_H__

#include <Arduino_USBHostMbed5.h>
#include <string>
#include <list>


#include "configs.h"
#include "Motor.h"
#include "Sequence.h"

namespace MyRobot
{   
  typedef enum
  {
    CONFIG_OK = 0,
    CONFIG_NO_USB_STORAGE,
    CONFIG_MOUNT_FAILURE,
    CONFIG_NO_CONFIG_FOUND,
    CONFIG_NO_SEQUENCE_FOLDER,
    CONFIG_BAD_JSON,
    CONFIG_TOO_LARGE,
    CONFIG_IO_FAILURE,
    CONFIG_PARSE_FAILURE,
    CONFIG_NO_SEQUENCE_FOUND,
    CONFIG_UNKNOWN_ERROR
  } CONFIG_ERROR;

  class ConfigUtil
  {
  public:
    static ConfigUtil* getInstance();
    ConfigUtil(const ConfigUtil&) = delete;
    ConfigUtil& operator=(const ConfigUtil&) = delete;

    void getBaseMotorConfig(MotorConfig& config);
    void getTower1MotorConfig(MotorConfig& config);
    void getTower2MotorConfig(MotorConfig& config);
    void getTower3MotorConfig(MotorConfig& config);
    void getEarMotorConfig(MotorConfig& config);

    CONFIG_ERROR updateBaseMotorConfig(const MotorConfig& config);
    CONFIG_ERROR updateTower1MotorConfig(const MotorConfig& config);
    CONFIG_ERROR updateTower2MotorConfig(const MotorConfig& config);
    CONFIG_ERROR updateTower3MotorConfig(const MotorConfig& config);
    CONFIG_ERROR updateEarMotorConfig(const MotorConfig& config);

    CONFIG_ERROR checkConfigs();
    CONFIG_ERROR initilize();

    std::list<std::string> getAnimationList() { return animationList_; }
    CONFIG_ERROR getSequenceByName(const std::string& animation, Sequence& sequence);
  private:
    ConfigUtil();
    CONFIG_ERROR flushConfigs();
    void flushToFile();
  private:
    static ConfigUtil* instance_;
    USBHostMSD* msd_;
    MotorConfig config_base_;
    MotorConfig config_tower1_;
    MotorConfig config_tower2_;
    MotorConfig config_tower3_;
    MotorConfig config_ear_;
    std::list<Sequence> sequenceList_;
    std::list<std::string> animationList_;
  };
}

#endif    //__CONFIGUTIL_H__
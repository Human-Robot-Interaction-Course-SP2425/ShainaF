#include "ConfigUtil.h"
#include <stdint.h>

#include <Arduino.h>
#include <FATFileSystem.h>
#include <ArduinoJson.h>


namespace MyRobot
{ 
  mbed::FATFileSystem usb("usb");

  ConfigUtil* ConfigUtil::instance_ = nullptr;

  ConfigUtil* ConfigUtil::getInstance()
  {
    if (nullptr == instance_)
    {
      instance_ = new ConfigUtil();
    }

    return instance_;
  }

  ConfigUtil::ConfigUtil()
    : msd_(nullptr)
  {
  }

  CONFIG_ERROR ConfigUtil::checkConfigs()
  {
    return CONFIG_OK;
  }

  CONFIG_ERROR ConfigUtil::initilize()
  {
    int tries = 0;

    if (msd_ == nullptr)
    {
      msd_ = new USBHostMSD();
    }

    pinMode(PA_15, OUTPUT);
    digitalWrite(PA_15, HIGH);

    while (!msd_->connect())
    {
      if (++tries > 5)
      {
        return CONFIG_NO_USB_STORAGE;
      }
      else
      {
        delay(1000);
      }
    }

    int err = usb.mount(msd_);
    if (err)
    {
      return CONFIG_MOUNT_FAILURE;
    }

    DIR* d = opendir("/usb/config/Sequences/");
    if (!d)
    {
      return CONFIG_NO_SEQUENCE_FOLDER;
    }
    
    struct dirent* entry;
    while ((entry = readdir(d)) != NULL)
    {
      std::string filename = entry->d_name;
      if (filename.find(".json") != std::string::npos)
      {
        std::string filePath("/usb/config/Sequences/");
        filePath += filename;
        auto openAndParseSequence = [](const std::string& filePath, Sequence& sequence)
        {
          FILE* fp = fopen(filePath.c_str(), "r");
          if (fp)
          {
            fseek(fp, 0, SEEK_END);
            long fileSize = ftell(fp);
            rewind(fp);

            char* buffer = new char[fileSize];
            if (buffer)
            {
              size_t result = fread(buffer, 1, fileSize, fp);
              if (result == fileSize)
              {
                buffer[fileSize] = '\0';

                DynamicJsonDocument doc(2048);
                DeserializationError error = deserializeJson(doc, buffer);
                if (!error)
                {
                  std::string animation = doc["animation"];
                  JsonArray frameList = doc["frame_list"];
                  
                  
                  sequence.animation_ = animation;
                  for (JsonObject frame : frameList)
                  {
                    float millis = frame["millis"];
                    JsonArray positions = frame["positions"];
                    Frame frm(millis);
                    for (JsonObject position : positions)
                    {
                      std::string dof = position["dof"];
                      float pos = position["pos"];
                      Position posStruct;
                      if (dof == "base")
                      {
                        posStruct.part_ = BASE;
                      }
                      else if (dof == "tower_1")
                      {
                        posStruct.part_ = TOWER_1;
                      }
                      else if (dof == "tower_2")
                      {
                        posStruct.part_ = TOWER_2;
                      }
                      else if (dof == "tower_3")
                      {
                        posStruct.part_ = TOWER_3;
                      }
                      else if (dof == "ear")
                      {
                        posStruct.part_ = EAR;
                      }
                      else
                      {
                        posStruct.part_ = MAX_PARTS_TYPES;
                      }
                      posStruct.position_ = pos;
                      frm.addPosition(posStruct);
                    }
                    sequence.appendList(frm);
                  }
                }
              }
            }
            delete [] buffer;
          }
          fclose(fp);
        };
        Sequence seq;
        openAndParseSequence(filePath, seq);

        if (seq.animation_ != "Unknown")
        {
          sequenceList_.push_back(seq);
          animationList_.push_back(seq.animation_);
        }
      }
    }

    closedir(d);
    FILE *fp = fopen("/usb/config/robot_config.json", "r");
    if (!fp)
    {
      return CONFIG_NO_CONFIG_FOUND;
    }

    fseek(fp, 0, SEEK_END);
    long fileSize = ftell(fp);
    rewind(fp);

    char* buffer = new char[fileSize];
    if (buffer == nullptr)
    {
      fclose(fp);
      return CONFIG_TOO_LARGE;
    }

    size_t result = fread(buffer, 1, fileSize, fp);
    if (result != fileSize)
    {
      delete [] buffer;
      fclose(fp);
      return CONFIG_IO_FAILURE;
    }

    buffer[fileSize] = '\0';
    
    DynamicJsonDocument doc(2048);
    DeserializationError error = deserializeJson(doc, buffer);
    if (error)
    {
      delete [] buffer;
      fclose(fp);
      return CONFIG_PARSE_FAILURE;
    }

    JsonArray motors = doc["motors"];
    size_t i = 0;
    for (JsonObject obj : motors)
    {
      if (i > 5)
      {
        break;
      }

      auto type = obj["type"].as<uint8_t>();
      auto id = obj["id"].as<uint8_t>();
      auto reset_pos = obj["reset_position"].as<float>();
      auto range_pos_low = obj["range_position_low"].as<float>();
      auto range_pos_high = obj["range_position_high"].as<float>();

      i++;

      switch (type)
      {
        case BASE:
        {
          config_base_.id = id;
          config_base_.reset_pos = reset_pos;
          config_base_.range_pos[0] = range_pos_low;
          config_base_.range_pos[1] = range_pos_high;
          break;
        }
        case TOWER_1:
        {
          config_tower1_.id = id;
          config_tower1_.reset_pos = reset_pos;
          config_tower1_.range_pos[0] = range_pos_low;
          config_tower1_.range_pos[1] = range_pos_high;
          break;
        }
        case TOWER_2:
        {
          config_tower2_.id = id;
          config_tower2_.reset_pos = reset_pos;
          config_tower2_.range_pos[0] = range_pos_low;
          config_tower2_.range_pos[1] = range_pos_high;
          break;
        }
        case TOWER_3:
        {
          config_tower3_.id = id;
          config_tower3_.reset_pos = reset_pos;
          config_tower3_.range_pos[0] = range_pos_low;
          config_tower3_.range_pos[1] = range_pos_high;
          break;
        }
        case EAR:
        {
          config_ear_.id = id;
          config_ear_.reset_pos = reset_pos;
          config_ear_.range_pos[0] = range_pos_low;
          config_ear_.range_pos[1] = range_pos_high;
          break;
        }
        default:
        {
          break;
        }
      }
    }

    delete [] buffer;
    fclose(fp);
    return CONFIG_OK;
  }

  void ConfigUtil::getBaseMotorConfig(MotorConfig& config)
  {
    config.id = config_base_.id;
    config.reset_pos = config_base_.reset_pos;
    config.range_pos[0] = config_base_.range_pos[0];
    config.range_pos[1] = config_base_.range_pos[1];
  }

  void ConfigUtil::getTower1MotorConfig(MotorConfig& config)
  {
    config.id = config_tower1_.id;
    config.reset_pos = config_tower1_.reset_pos;
    config.range_pos[0] = config_tower1_.range_pos[0];
    config.range_pos[1] = config_tower1_.range_pos[1];
  }

  void ConfigUtil::getTower2MotorConfig(MotorConfig& config)
  {
    config.id = config_tower2_.id;
    config.reset_pos = config_tower2_.reset_pos;
    config.range_pos[0] = config_tower2_.range_pos[0];
    config.range_pos[1] = config_tower2_.range_pos[1];
  }

  void ConfigUtil::getTower3MotorConfig(MotorConfig& config)
  {
    config.id = config_tower3_.id;
    config.reset_pos = config_tower3_.reset_pos;
    config.range_pos[0] = config_tower3_.range_pos[0];
    config.range_pos[1] = config_tower3_.range_pos[1];
  }

  void ConfigUtil::getEarMotorConfig(MotorConfig& config)
  {
    config.id = config_ear_.id;
    config.reset_pos = config_ear_.reset_pos;
    config.range_pos[0] = config_ear_.range_pos[0];
    config.range_pos[1] = config_ear_.range_pos[1];
  }

  CONFIG_ERROR ConfigUtil::updateBaseMotorConfig(const MotorConfig& config)
  {
    config_base_.id = config.id;
    config_base_.reset_pos = config.reset_pos;
    config_base_.range_pos[0] = config.range_pos[0];
    config_base_.range_pos[1] = config.range_pos[1];

    flushToFile();
    return  CONFIG_OK;
  }

  CONFIG_ERROR ConfigUtil::updateTower1MotorConfig(const MotorConfig& config)
  {
    config_tower1_.id = config.id;
    config_tower1_.reset_pos = config.reset_pos;
    config_tower1_.range_pos[0] = config.range_pos[0];
    config_tower1_.range_pos[1] = config.range_pos[1];

    flushToFile();
    return  CONFIG_OK;
  }

  CONFIG_ERROR ConfigUtil::updateTower2MotorConfig(const MotorConfig& config)
  {
    config_tower2_.id = config.id;
    config_tower2_.reset_pos = config.reset_pos;
    config_tower2_.range_pos[0] = config.range_pos[0];
    config_tower2_.range_pos[1] = config.range_pos[1];

    flushToFile();
    return  CONFIG_OK;
  }

  CONFIG_ERROR ConfigUtil::updateTower3MotorConfig(const MotorConfig& config)
  {
    config_tower3_.id = config.id;
    config_tower3_.reset_pos = config.reset_pos;
    config_tower3_.range_pos[0] = config.range_pos[0];
    config_tower3_.range_pos[1] = config.range_pos[1];

    flushToFile();
    return  CONFIG_OK;
  }

  CONFIG_ERROR ConfigUtil::updateEarMotorConfig(const MotorConfig& config)
  {
    config_ear_.id = config.id;
    config_ear_.reset_pos = config.reset_pos;
    config_ear_.range_pos[0] = config.range_pos[0];
    config_ear_.range_pos[1] = config.range_pos[1];

    flushToFile();
    return  CONFIG_OK;
  }

  CONFIG_ERROR ConfigUtil::getSequenceByName(const std::string& animation, Sequence& sequence)
  {
    std::list<Sequence>::iterator itr;
    for (itr = sequenceList_.begin(); itr != sequenceList_.end(); itr++)
    {
      if (itr->animation_ == animation)
      {
        sequence = *itr;
        return CONFIG_OK;
      }
    }
    return CONFIG_NO_SEQUENCE_FOUND;
  }

  void ConfigUtil::flushToFile()
  {
    DynamicJsonDocument doc(2048);
    JsonArray motors = doc.createNestedArray("motors");

    auto fillinConfigs = [](JsonArray& motors, PARTTYPE type, const MotorConfig& config)
    {
      JsonObject motor = motors.createNestedObject();
      motor["type"] = type;
      motor["id"] = config.id;
      motor["reset_position"] = config.reset_pos;
      motor["range_position_low"] = config.range_pos[0];
      motor["range_position_high"] = config.range_pos[1];
    };
     
    fillinConfigs(motors, BASE, config_base_);
    fillinConfigs(motors, TOWER_1, config_tower1_);
    fillinConfigs(motors, TOWER_2, config_tower2_);
    fillinConfigs(motors, TOWER_3, config_tower3_);
    fillinConfigs(motors, EAR, config_ear_);

    char output[2048];
    serializeJson(doc, output, sizeof(output));

    FILE *fp = fopen("/usb/config/robot_config.json", "w");
    if (!fp)
    {
      return;
    }

    fputs(output, fp);
    fclose(fp);
  }
}
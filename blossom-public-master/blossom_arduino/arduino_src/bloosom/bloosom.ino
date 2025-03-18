#include <DynamixelShield.h>
#include "Robot.h"
#include "ConfigUtil.h"
#include "Frame.h"
#include "SequencePlayer.h"

//Serial: The serial port on Dynamixel Shield
//Serial2: The serial port on Arduono board.

//#define DEBUG_SERIAL  Serial
//#define COMMAND_SERIAL  Serial2

#define DEBUG_SERIAL  Serial
#define COMMAND_SERIAL  Serial2

using namespace MyRobot;

#define MAX_BAUD  5
const int32_t buad[MAX_BAUD] = {57600, 115200, 1000000, 2000000, 3000000};

uint8_t base_id = 0x01;
uint8_t tower1_id = 0x02;
uint8_t tower2_id = 0x03;
uint8_t tower3_id = 0x04;
uint8_t ear_id = 0x05;

const float reset_pos_base = 0;
const float reset_pos_tower1 = 50;
const float reset_pos_tower2 = 50;
const float reset_pos_tower3 = 50;
const float reset_pos_ear = 100;

const float range_pos_base[2] = {0, 360};
const float range_pos_tower1[2] = {0, 140};
const float range_pos_tower2[2] = {0, 140};
const float range_pos_tower3[2] = {0, 140};
const float range_pos_ear[2] = {0, 140};

DynamixelShield dxl;
MotorImpl motor_base_impl(base_id, dxl);
MotorImpl motor_tower1_impl(tower1_id, dxl);
MotorImpl motor_tower2_impl(tower2_id, dxl);
MotorImpl motor_tower3_impl(tower3_id, dxl);
//MotorImpl motor_ear_impl(ear_id, dxl);

Motor motor_base(BASE, reset_pos_base, range_pos_base[0], range_pos_base[1], motor_base_impl);
Motor motor_tower1(TOWER_1, reset_pos_tower1, range_pos_tower1[0], range_pos_tower1[1], motor_tower1_impl);
Motor motor_tower2(TOWER_2, reset_pos_tower2, range_pos_tower2[0], range_pos_tower2[1], motor_tower2_impl);
Motor motor_tower3(TOWER_3, reset_pos_tower3, range_pos_tower3[0], range_pos_tower3[1], motor_tower3_impl);
//Motor motor_ear(EAR, reset_pos_ear, range_pos_ear[0], range_pos_ear[1], motor_ear_impl);

Robot myRobot;

void setup() 
{
  DEBUG_SERIAL.begin(115200);
  COMMAND_SERIAL.begin(115200);
  delay(2000);


  DEBUG_SERIAL.print("Initializing Dynamixel Shield... ");  
  dxl.begin(57600);
  dxl.setPortProtocolVersion(2.0);
  dxl.ping(1);

  DEBUG_SERIAL.print("Assemble Robot... ");

  auto assembleMotorToRobot = [](PARTTYPE type, Motor& motor)
  {
    MotorConfig config;
    switch (type)
    {
      case BASE:
      {
        ConfigUtil::getInstance()->getBaseMotorConfig(config);
        break;
      }
      case TOWER_1:
      {
        ConfigUtil::getInstance()->getTower1MotorConfig(config);
        break;
      }
      case TOWER_2:
      {
        ConfigUtil::getInstance()->getTower2MotorConfig(config);
        break;
      }
      case TOWER_3:
      {
        ConfigUtil::getInstance()->getTower3MotorConfig(config);
        break;
      }
      case EAR:
      {
        ConfigUtil::getInstance()->getEarMotorConfig(config);
        break;
      }
      default:
      {
        break;
      }
    }

    motor.setType(type);
    motor.setResetPos(config.reset_pos);
    motor.setRangePosLow(config.range_pos[0]);
    motor.setRangePosHigh(config.range_pos[1]);

    myRobot.attachMotor2Robot(&motor);
  };

  assembleMotorToRobot(BASE, motor_base);
  assembleMotorToRobot(TOWER_1, motor_tower1);
  assembleMotorToRobot(TOWER_2, motor_tower2);
  assembleMotorToRobot(TOWER_3, motor_tower3);
  //assembleMotorToRobot(EAR, motor_ear);

  myRobot.initialize();


  
  auto err = ConfigUtil::getInstance()->initilize();
  if (err != CONFIG_OK)
  {
    DEBUG_SERIAL.print("CONFIGUTIL INITIALIZE NOT OK");
    DEBUG_SERIAL.println(err);
  }
  else
  {
    DEBUG_SERIAL.println("CONFIGUTIL INITIALIZE OK");
  }
  
  displayMenu();
  
}
void normalMode()
{
  //TODO:
}

void diagnosticMode()
{
  //TODO:
}

void motorInformation()
{
  DEBUG_SERIAL.println(">>>>>>GET MOTOR(s) INFORMATION<<<<<<");
  DEBUG_SERIAL.println("Step-1: Re-scan online motors...");
  int8_t index = 0;
  int8_t found_dynamixel = 0;
  uint8_t motor_id;
  uint8_t ids[255];

  for (int8_t protocol = 1; protocol < 3; protocol++)
  {
    dxl.setPortProtocolVersion((float)protocol);
    DEBUG_SERIAL.print("\tSCAN PROTOCOL ");
    DEBUG_SERIAL.println(protocol);

    for (index = 0; index < MAX_BAUD; index++)
    {
      DEBUG_SERIAL.print("\tSCAN BAUDRATE ");
      DEBUG_SERIAL.println(buad[index]);
      dxl.begin(buad[index]);
      for (int id = 0; id < DXL_BROADCAST_ID; id++)
      {
        if (dxl.ping(id)) 
        {
          DEBUG_SERIAL.print("\tID : ");
          DEBUG_SERIAL.print(id);
          DEBUG_SERIAL.print(", Model Number: ");
          DEBUG_SERIAL.println(dxl.getModelNumber(id));
          ids[found_dynamixel++] = id;
        }
      }
    }
  }

  DEBUG_SERIAL.println("Step-3: Please modify the robot_config.json manually acording to the motors found.");
  for (uint8_t i = 0; i < found_dynamixel; i++)
  {
    DEBUG_SERIAL.println(ids[i]);
  }  
}

void demoMode()
{
  float angle = 0;
  DEBUG_SERIAL.println(">>>>>>DEMO MODE<<<<<<");
  Motor* pMotor = myRobot.getMotor(BASE);

  for (int i = 0; i < 9; i++)
  {
    DEBUG_SERIAL.print("Will Move From ");
    DEBUG_SERIAL.println(pMotor->getAngle());
    DEBUG_SERIAL.print("To: ");
    DEBUG_SERIAL.println(angle);
    pMotor->moveAngle(angle);
    delay(1000);

    angle += 45;
    DEBUG_SERIAL.print("Present Position(Degree) : ");
    DEBUG_SERIAL.println(pMotor->getAngle());
    delay(1000);
    
  }
}

void loop() 
{
  //demoMode();

  if (DEBUG_SERIAL.available() > 0)
  {
    char choice = DEBUG_SERIAL.read();

    switch (choice)
    {
      case 'N':
      case 'n':
      {
        DEBUG_SERIAL.println("Start Normal Mode.");
        break;
      }
      case 'D':
      case 'd':
      {
        DEBUG_SERIAL.println("Start Diagnostic Mode.");
        break;
      }
      case 'I':
      case 'i':
      {
        motorInformation();
        break;
      }
      case 'C':
      case 'c':
      {
        dumpConfigs();
        break;
      }
      case 'E':
      case 'e':
      {
        demoMode();
        break;
      }
      case 'P':
      case 'p':
      {
        performSequence(true);
        break;
      }
      case 'S':
      case 's':
      {
        dumpSequences(false);
        break;
      }
      case 'T':
      case 't':
      {
        dumpSequences(true);
        performSequence(false);
        break;
      }
      default:
      {
        DEBUG_SERIAL.println("Invalid Option. Please try again.");
        displayMenu();
        break;
      }
    }
  }

}

void dumpConfigs()
{
  auto printOutConfigs = [](PARTTYPE type, const MotorConfig& config) 
  {
    char logBuff[1024];
    snprintf(logBuff, sizeof(logBuff),"Motor: <%d>\t ID=<%d>\t RESET_POSITION=<%f>\t RANGE_POS=[<%f>, <%f>]\r\n", 
                type, config.id, config.reset_pos, config.range_pos[0], config.range_pos[1]);
    DEBUG_SERIAL.print(logBuff);
  };

  MotorConfig config;
  ConfigUtil::getInstance()->getBaseMotorConfig(config);
  printOutConfigs(BASE, config);

  ConfigUtil::getInstance()->getTower1MotorConfig(config);
  printOutConfigs(TOWER_1, config);

  ConfigUtil::getInstance()->getTower2MotorConfig(config);
  printOutConfigs(TOWER_2, config);

  ConfigUtil::getInstance()->getTower3MotorConfig(config);
  printOutConfigs(TOWER_3, config);

  ConfigUtil::getInstance()->getEarMotorConfig(config);
  printOutConfigs(EAR, config);
}

void dumpSequences(bool testToExecute)
{
  auto printOutSequence = [](const std::string& seqName)
  {
    Sequence sequence;
    if (CONFIG_OK == ConfigUtil::getInstance()->getSequenceByName(seqName, sequence))
    {
      auto frmList = sequence.getFrameList();
      std::list<Frame>::iterator itr;
      for (itr = frmList.begin(); itr != frmList.end(); itr++)
      {
        auto durationMs = itr->getDurationMs();
        DEBUG_SERIAL.print("Duration (ms): ");
        DEBUG_SERIAL.println(durationMs);
        auto positions = itr->getPositions();
        std::vector<Position>::iterator itr1;
        for (itr1 = positions.begin(); itr1 != positions.end(); itr1++)
        {
          DEBUG_SERIAL.print("Part: ");
          DEBUG_SERIAL.println(itr1->part_);
          DEBUG_SERIAL.print("Position: ");
          DEBUG_SERIAL.println(itr1->position_);
        }
      }

      DEBUG_SERIAL.print("Intervals: ");
      SequencePlayer::getInstance()->loadSequence(sequence);
      auto intervals = SequencePlayer::getInstance()->getIntervalSeries();
      auto itr1 = intervals.begin();
      for (itr1; itr1 != intervals.end(); itr1++)
      {
        DEBUG_SERIAL.print(*itr1);
        DEBUG_SERIAL.print(",");
      }
      DEBUG_SERIAL.println(".");
    }
  };
  DEBUG_SERIAL.println(">>>>>>ALL LOADED SEQUENCES<<<<<<");
  auto animations = ConfigUtil::getInstance()->getAnimationList();
  std::list<std::string>::const_iterator itr;
  for (itr = animations.begin(); itr != animations.end(); itr++)
  {
    DEBUG_SERIAL.print("SEQUENCE: ");
    DEBUG_SERIAL.println(itr->c_str());
    printOutSequence(*itr);
    DEBUG_SERIAL.println("------------");
  }
}

void performSequence(bool onRealMotor)
{
  SequencePlayer::PRINTOUTFUNCTION printOutFunc = [](std::string& str)
  {
      DEBUG_SERIAL.println(str.c_str());
  };
  auto animations = ConfigUtil::getInstance()->getAnimationList();
  std::list<std::string>::const_iterator itr;
  for (itr = animations.begin(); itr != animations.end(); itr++)
  {
    Sequence sequence;
    if (CONFIG_OK == ConfigUtil::getInstance()->getSequenceByName(*itr, sequence))
    {
      SequencePlayer::getInstance()->loadSequence(sequence);
      SequencePlayer::getInstance()->play(
        myRobot,
        printOutFunc,
        onRealMotor
      );
    }
  }
}

void displayMenu()
{
  DEBUG_SERIAL.println("Robot Ready, select the mode:");
  DEBUG_SERIAL.println("n: Start Normal Mode");
  DEBUG_SERIAL.println("d: Diagnostic Mode");
  DEBUG_SERIAL.println("i: Motor Calibration");
  DEBUG_SERIAL.println("e: Demo Mode");
  DEBUG_SERIAL.println("c: Print Configs");
  DEBUG_SERIAL.println("s: Print All Sequences");
  DEBUG_SERIAL.println("t: Test All Sequnences on Stub Motor");
  DEBUG_SERIAL.println("p: Perform Sequences");
  DEBUG_SERIAL.println("Enter the letter of your choice:");
}

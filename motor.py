import time
import random

ENGINE_SPEED_MAX = 25700
IDLE_ENGINE_SPEED_MAX = 4000
ISCVP_MAX = 510
ENV_AIR_PRESSURE = 101.9
FULL_POWER_NEWTON = 1800
ENGINE_FORCE_PER_STEP = FULL_POWER_NEWTON / 125
HUMAN_WEIGHT = 70
MOTOR_WEIGHT = 187
ENVIRONMENT_FRICTION = 2
WIND_RESISTANCE_PARAM = 5
GEAR_RATIO = [10000, 9, 7, 6, 5.5, 5]
VEHICLE_SPEED_MAX = 240
SDC_MAX = 50
EXCVAP_MAX = 125
ENV_TEMPERATURE = 26

class Motor:
    def __init__(self):
        self.env_param = {'AP': ENV_AIR_PRESSURE, 'FR': ENVIRONMENT_FRICTION, 'TP': ENV_TEMPERATURE}
        self.last_time = 0.0
        self.now_time = 0.0
        self.engine_open = False
        self.start_button = False
        self.engine_working = False
        self.throttle_position = 0
        self.rpm = 0
        self.speed = 0
        self.gear = 0
        self.intake_air_pressure = 150
        self.clutch = False
        self.neutral = False
        self.idle_speed_control_valve = 384
        self.desired_idle_speed = self.idle_speed_control_valve * IDLE_ENGINE_SPEED_MAX / ISCVP_MAX
        self.steering_damper_current = 0
        self.exhaust_control_valve = 0
        self.mode_1 = False
        self.mode_2 = False
        self.o2_sensor = 0
        self.battery_voltage = 0
        self.air_supply_solenoid_valve = False
        self.fuel_level = 100
        self.fuel_cost = 0
        self.engine_coolant_temperature = ENV_TEMPERATURE

    def getEngineOpen(self):
        return self.engine_open

    def openEngine(self):
        self.engine_open = True
        self.neutral = False if self.gear else True
        self.battery_voltage = 20

    def closeEngine(self):
        self.engine_working = False
        self.engine_open = False
        self.last_time = 0.0
        self.now_time = 0.0
        self.rpm = 0
        self.speed = 0
        self.throttle_position = 0
        self.intake_air_pressure = 150
        self.clutch = False
        self.neutral = False
        self.steering_damper_current = 0
        self.exhaust_control_valve = 0
        self.mode_1 = False
        self.mode_2 = False
        self.o2_sensor = 0
        self.battery_voltage = 0
        self.air_supply_solenoid_valve = False

    def pressStartButton(self):
        if self.engine_open:
            if self.start_button:
                self.start_button = False
            else:
                self.start_button = True
                self.engine_working = True
                self.o2_sensor = 5

    def pullClutch(self):
        if self.engine_open:
            if self.clutch:
                self.clutch = False
            else:
                self.clutch = True

    def gearControl(self, step):
        self.gear += step
        if self.gear < 0:
            self.gear = 0
        elif self.gear > 5:
            self.gear = 5
        
        if self.engine_open:
            self.neutral = False if self.gear else True

    def recompute_attr(self):
        if self.engine_working:
            self.now_time = time.time()
            if not self.last_time:
                self.last_time = self.now_time

            # simulate environment parameter
            if not random.randint(0, 200) and self.speed:
                self.env_param['AP'] += 0.1 * random.randint(-5, 5)
                self.env_param['FR'] += 0.2 * random.randint(-1, 1)
                self.env_param['TP'] += 0.1 * random.randint(-10, 10)
                self.o2_sensor += 0.02 * random.randint(-1, 1)
                self.o2_sensor = 5 if self.o2_sensor > 5 else self.o2_sensor
                self.o2_sensor = 0 if self.o2_sensor < 0 else self.o2_sensor
                self.battery_voltage += 0.1 * random.randint(-1, 1)
                self.battery_voltage = 20 if self.battery_voltage > 20 else self.battery_voltage
                self.battery_voltage = 0 if self.battery_voltage < 0 else self.battery_voltage
                self.air_supply_solenoid_valve = False if self.air_supply_solenoid_valve else True

            f_eng = self.throttle_position * ENGINE_FORCE_PER_STEP
            f_load = self.env_param['FR'] + WIND_RESISTANCE_PARAM * self.speed
            accelerate = (f_eng - f_load) / (MOTOR_WEIGHT + HUMAN_WEIGHT)
            self.speed += accelerate * (self.now_time - self.last_time) * 3.6
            #print f_eng, f_load, accelerate, self.speed
            if self.speed < 0:
                self.speed = 0
            elif self.speed > VEHICLE_SPEED_MAX:
                self.speed = VEHICLE_SPEED_MAX

            self.rpm = round((self.desired_idle_speed + self.speed * GEAR_RATIO[self.gear] * 1000 / 60), 1)
            if self.rpm > ENGINE_SPEED_MAX:
                self.rpm = ENGINE_SPEED_MAX

            if not self.gear:
                self.speed = 0
            
            self.intake_air_pressure = 150 - 170 * (self.throttle_position / 125)
            self.steering_damper_current = round(self.speed * SDC_MAX / VEHICLE_SPEED_MAX)
            self.exhaust_control_valve = round(self.rpm * EXCVAP_MAX / ENGINE_SPEED_MAX, 1)

            self.fuel_cost += self.throttle_position
            if self.fuel_cost > 10000:
                self.fuel_level -= 0.5
                self.fuel_cost = 0
                self.fuel_level = 0 if self.fuel_level < 0 else self.fuel_level

            self.engine_coolant_temperature += (70 * (1.0 + self.throttle_position/125))
            cooldown_param = 0.5 + (self.speed/VEHICLE_SPEED_MAX)*0.122
            self.engine_coolant_temperature = self.engine_coolant_temperature * (1-cooldown_param) + self.env_param['TP'] * cooldown_param
            
            self.last_time = self.now_time

    def openThrottle(self, step):
        if self.engine_working:
            tps = self.throttle_position + step
            if tps <= 125 and tps >= 0:
                self.throttle_position = tps
            elif tps > 125:
                self.throttle_position = 125
            elif tps < 0:
                self.throttle_position = 0

    def controlISCVP(self, step):
        if self.idle_speed_control_valve + step >= 0 and self.idle_speed_control_valve + step <= ISCVP_MAX:
            self.idle_speed_control_valve += step
            self.desired_idle_speed = self.idle_speed_control_valve * IDLE_ENGINE_SPEED_MAX / ISCVP_MAX
    
    def modeSelection(self, mode):
        if self.engine_open:
            if mode == 1:
                self.mode_1 = False if self.mode_1 else True
            elif mode == 2:
                self.mode_2 = False if self.mode_2 else True

    def __str__(self):
        if self.engine_working:
            engine_state = 'ON1'
        elif self.engine_open:
            engine_state = 'ON'
        else:
            engine_state = 'OFF'
        rtn = 'VS: ' + str(round(self.speed))
        rtn += ' ES: ' + str(self.rpm)
        rtn += ' TPS: ' + str(self.throttle_position)
        rtn += ' IAP: ' + str(self.intake_air_pressure)
        rtn += ' AP: ' + str(self.env_param['AP'])
        rtn += ' ECT: ' + str(round(self.engine_coolant_temperature))
        rtn += ' BV: ' + str(self.battery_voltage)
        rtn += ' O2: ' + str(self.o2_sensor)
        rtn += ' GP: ' + str(self.gear)
        rtn += ' DIS: ' + str(self.desired_idle_speed)
        rtn += ' ISCVP: ' + str(self.idle_speed_control_valve)
        rtn += ' FL: ' + str(self.fuel_level)
        rtn += ' SDC: ' + str(self.steering_damper_current)
        rtn += ' EXCV: ' + str(self.exhaust_control_valve)
        rtn += ' MS1: ' + ('ON' if self.mode_1 else 'OFF')
        rtn += ' MS2: ' + ('ON' if self.mode_2 else 'OFF')
        rtn += ' PAIRCV: ' + ('ON' if self.air_supply_solenoid_valve else 'OFF')
        rtn += ' IS: ' + engine_state
        rtn += ' CL: ' + ('ON' if self.clutch else 'OFF')
        rtn += ' N: ' + ('ON' if self.neutral else 'OFF')
        rtn += ' SB: ' + ('ON' if self.start_button else 'OFF')
        return rtn

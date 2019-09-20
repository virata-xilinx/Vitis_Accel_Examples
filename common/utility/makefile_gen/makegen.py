#!/usr/bin/env python
from sys import argv
import json
import glob
import os
import re
import subprocess

#ini flags
config_file = 0

def create_params(target,data):    
    target.write("# Points to Utility Directory\n")
    dirName = os.getcwd()
    dirNameList = list(dirName.split("/"))
    dirNameIndex = dirNameList.index("Vitis_Accel_Examples")
    diff = len(dirNameList) - dirNameIndex - 1
    target.write("COMMON_REPO = ")
    while diff > 0:
	target.write("../")
	diff -= 1 
    target.write("\n")
    target.write("PWD = $(shell readlink -f .)\n")
    target.write("ABS_COMMON_REPO = $(shell readlink -f $(COMMON_REPO))\n")
    target.write("\n")
    target.write("TARGET := hw\n")
    target.write("HOST_ARCH := x86\n")
    target.write("SYSROOT := \n")
    target.write("DEVICE = xilinx_u200_xdma_201920_1\n")
    target.write("\n")
    target.write("include ./utils.mk\n")
    target.write("\n")
    target.write("XSA := $(call device2xsa, $(DEVICE))\n")
    target.write("TEMP_DIR := ./_x.$(TARGET).$(XSA)\n")
    target.write("BUILD_DIR := ./build_dir.$(TARGET).$(XSA)\n")
    target.write("\n")

    target.write("ifeq ($(HOST_ARCH), x86)\n")
    target.write("\tCXX := $(XILINX_VITIS)/bin/xcpp\n")
    target.write("else ifeq ($(HOST_ARCH), aarch64)\n")
    target.write("\tCXX := $(XILINX_VITIS)/gnu/aarch64/lin/aarch64-linux/bin/aarch64-linux-gnu-g++\n")
    target.write("else ifeq ($(HOST_ARCH), aarch32)\n")
    target.write("\tCXX := $(XILINX_VITIS)/gnu/aarch32/lin/gcc-arm-linux-gnueabi/bin/arm-linux-gnueabihf-g++\n")
    target.write("endif\n\n")
    target.write("VPP := ")
    target.write("v++\n")
    target.write("\n")
    add_includes1(target, data)
    add_includes2(target, data) 
    if "config_make" in data:
	target.write("include ")
	target.write(data["config_make"])
	target.write("\n\n")    
    target.write("CXXFLAGS += $(opencl_CXXFLAGS) -Wall -O0 -g -std=c++14\n")
    target.write("LDFLAGS += $(opencl_LDFLAGS)\n")
    target.write("\n")
    return

#adding lib.mk
def add_includes1(target, data):
    target.write("#Include Libraries\n")
    target.write("include $(ABS_COMMON_REPO)/common/includes/opencl/opencl.mk\n")
    if "host" in data:
	if "compiler" in data["host"]:	
    		if "includepaths" in data["host"]["compiler"]:
        		for path in data["host"]["compiler"]["includepaths"]:
            			target.write("include "+ path.replace("REPO_DIR","$(ABS_COMMON_REPO)"))
            			#target.write(lib)
            			target.write("/")
            			target.write(path.split("/")[-1])
            			target.write(".mk")
            			target.write("\n")
    return

def add_includes2(target, data):
    if "host" in data:
	if "compiler" in data["host"]:		
    		if "includepaths" in data["host"]["compiler"]:
        		target.write("CXXFLAGS +=")
        		for path in data["host"]["compiler"]["includepaths"]:
            			target.write(" $(")
            			target.write(path.split("/")[-1])
            			target.write("_CXXFLAGS)")
        		target.write("\n")
        		target.write("LDFLAGS +=")
        		for path in data["host"]["compiler"]["includepaths"]:
            			target.write(" $(")
            			target.write(path.split("/")[-1])
            			target.write("_LDFLAGS)")
        		target.write("\n")
        		target.write("HOST_SRCS +=")
        		for path in data["host"]["compiler"]["includepaths"]:
            			target.write(" $(")
            			target.write(path.split("/")[-1])
            			target.write("_SRCS)")
    
     	if "linker" in data["host"]:
        	if "options" in data["host"]["linker"]:
            		target.write("\nCXXFLAGS +=")
            		for option in data["host"]["linker"]["options"]:
  	        		target.write(" ")
	        		target.write(option)
   	target.write("\n")                
   	return

def add_host_flags(target, data):
    target.write("HOST_SRCS += ")
    source_flag = 0
    if "sources" in data["host"]["compiler"]:
	for src in data["host"]["compiler"]["sources"]:
		if "src" in src.split("/"):
    			target.write(src+ " ")
			source_flag+=1
    if not source_flag:
	target.write("src/host.cpp\n")
    target.write("\n")
    target.write("# Host compiler global settings\n")  	
    target.write("CXXFLAGS += ")
    target.write("-fmessage-length=0")
        
    if "compiler" in data["host"]:
	if "options" in data["host"]["compiler"]:
	    target.write(data["host"]["compiler"]["options"])
    target.write("\n")	
    target.write("LDFLAGS += ")
    target.write("-lrt -lstdc++ ")
    target.write("\n\n")
    target.write("ifneq ($(HOST_ARCH), x86)\n")
    target.write("\tLDFLAGS += --sysroot=$(SYSROOT)\n")
    target.write("endif\n\n")
    return

def add_kernel_flags(target, data):
    target.write("# Kernel compiler global settings\n")
    target.write("CLFLAGS += ")
    target.write("-t $(TARGET) --platform $(DEVICE) --save-temps \n")   

    if "containers" in data:
        for con in data["containers"]:
            for acc in con["accelerators"]:
                if "max_memory_ports" in acc:
		    target.write("CLFLAGS += ")
                    target.write(" --max_memory_ports ")
                    target.write(acc["name"])
        	    target.write("\n")

    if "containers" in data:
        for con in data["containers"]:
            for acc in con["accelerators"]:
                if "clflags" in acc:
		    target.write("CLFLAGS +=")
		    flags = acc["clflags"].split(" ")
		    for flg in flags[0:]:
			target.write(" ")
			flg = flg.replace('PROJECT', '.')
			target.write(flg)
                    target.write("\n")
    
    if "compiler" in data["host"]:
        if "symbols" in data["host"]["compiler"]:
            target.write("\nCXXFLAGS +=")
            for sym in data["host"]["compiler"]["symbols"]:
                target.write(" ")
                target.write("-D")
                target.write(sym)
        target.write("\n")

    if "containers" in data:
        for con in data["containers"]:
            if  "ldclflags" in con:
		target.write("\n")
                target.write("# Kernel linker flags\n")
                target.write("LDCLFLAGS +=")
		ldclflags = con["ldclflags"].split(" ")
		for flg in ldclflags[0:]:
		    target.write(" ")
		    flg = flg.replace('PROJECT', '.')
		    target.write(flg)
            target.write("\n")

    #adding config files to linker
    for dirs,subdirs,files in os.walk("."):
	if "containers" in data:
		for con in data["containers"]:
			if con["name"]+".ini" in files:
				target.write("\n")
				target.write("# Adding config files to linker\n")
				target.write("LDCLFLAGS += ")
				target.write("--config "+con["name"]+".ini ")
    target.write("\n")
    target.write("EXECUTABLE = ")
    if "host_exe" in data["host"]:
        target.write(data["host"]["host_exe"])    
    else: 
        target.write("host")
    if "launch" in data:
    	target.write("\n")
        target.write("CMD_ARGS =")
	cmd_args = data["launch"][0]["cmd_args"].split(" ")
	for cmdargs in cmd_args[0:]:
	    target.write(" ")
            cmdargs = cmdargs.replace('BUILD', '$(BUILD_DIR)')
            cmdargs = cmdargs.replace('PROJECT', '.')
	    target.write(cmdargs)

    target.write("\nEXEC_CMD_ARGS += $(EXECUTABLE)\n")

    target.write("EXEC_CMD_ARGS += ")
    if "launch" in data:
        cmd_args = data["launch"][0]["cmd_args"].split(" ")
        for cmdargs in cmd_args[0:]:
            target.write(" ")
            cmdargs = cmdargs.replace('BUILD/', '')
            cmdargs = cmdargs.replace('PROJECT/', '')
            target.write(cmdargs)

    target.write("\n")

    target.write("EMCONFIG_DIR = $(TEMP_DIR)")
    target.write("\n\n")

    return

def add_containers(target, data):
    if "containers" in data:
	for con in data["containers"]:
	    target.write("BINARY_CONTAINERS += $(BUILD_DIR)/")
            target.write(con["name"])
            target.write(".xclbin\n")
	    if "accelerators" in con:
		for acc in con["accelerators"]:
		    target.write("BINARY_CONTAINER_")
                    target.write(con["name"])
                    target.write("_OBJS += $(TEMP_DIR)/") 
		    target.write(acc["name"])
                    target.write(".xo\n")       	
    target.write("\n")

def building_kernel(target, data):
    target.write("# Building kernel\n")
    if "containers" in data:
	for con in data["containers"]:
	    if "accelerators" in con:
		for acc in con["accelerators"]:
		    target.write("$(TEMP_DIR)/")
            	    target.write(acc["name"])
            	    target.write(".xo: ")
		    target.write(acc["location"])
		    target.write("\n")
                    target.write("\tmkdir -p $(TEMP_DIR)\n")
                    target.write("\t$(VPP) $(CLFLAGS) --temp_dir ")
                    target.write("$(TEMP_DIR) ")
                    target.write("-c -k ")
                    target.write(acc["name"])
                    target.write(" -I'$(<D)'")
                    target.write(" -o'$@' '$<'\n")
    if "containers" in data:
        for con in data["containers"]:
            target.write("$(BUILD_DIR)/")
            target.write(con["name"])
            target.write(".xclbin:")
            target.write(" $(BINARY_CONTAINER_")
            target.write(con["name"])
            target.write("_OBJS)\n")
            target.write("\tmkdir -p $(BUILD_DIR)\n")
            target.write("\t$(VPP) $(CLFLAGS) --temp_dir ")
            target.write("$(BUILD_DIR) ")
            target.write("-l $(LDCLFLAGS)")
            target.write(" -o'$@' $(+)\n")
    target.write("\n")
    return

def building_kernel_rtl(target, data):
    target.write("# Building kernel\n")
    if "containers" in data:
        for con in data["containers"]:
            target.write("$(BUILD_DIR)/")
            target.write(con["name"])
            target.write(".xclbin:")
            target.write(" $(BINARY_CONTAINER_")
            target.write(con["name"])
            target.write("_OBJS)\n")
            target.write("\tmkdir -p $(BUILD_DIR)\n")
            target.write("\t$(VPP) $(CLFLAGS) --temp_dir ")
            target.write("$(BUILD_DIR) ")
            target.write("-l $(LDCLFLAGS)")
            target.write(" -o'$@' $(+)\n\n")
    return

def building_host(target, data):
    target.write("# Building Host\n")
    target.write("$(EXECUTABLE): check-xrt $(HOST_SRCS) $(HOST_HDRS)\n")
    target.write("\t$(CXX) $(CXXFLAGS) $(HOST_SRCS) $(HOST_HDRS) -o '$@' $(LDFLAGS)\n")
    target.write("\n")
    target.write("emconfig:$(EMCONFIG_DIR)/emconfig.json\n")
    target.write("$(EMCONFIG_DIR)/emconfig.json:\n")
    target.write("\temconfigutil --platform $(DEVICE) --od $(EMCONFIG_DIR)")
    if "num_devices" in data:
        target.write(" --nd ")
        target.write(data["num_devices"])
    target.write("\n\n")        
    return

def profile_report(target):
    target.write("[Debug]\n")
    target.write("profile=true\n")

    return

def mk_clean(target, data):
    target.write("# Cleaning stuff\n")
    target.write("clean:\n")
    target.write("\t-$(RMDIR) $(EXECUTABLE) $(XCLBIN)/{*sw_emu*,*hw_emu*} \n")
    target.write("\t-$(RMDIR) profile_* TempConfig system_estimate.xtxt *.rpt *.csv \n")
    target.write("\t-$(RMDIR) src/*.ll _xocc_* .Xil emconfig.json dltmp* xmltmp* *.log *.jou *.wcfg *.wdb\n")
    target.write("\n")

    target.write("cleanall: clean\n")
    target.write("\t-$(RMDIR) build_dir* sd_card\n")
    target.write("\t-$(RMDIR) _x.* xclbin.run_summary qemu-memory-_* emulation/ _vimage/ pl* start_simulation.sh *.xclbin\n")
    if "output_files" in data:         
        target.write("\t-$(RMDIR) ")
        args = data["output_files"].split(" ")
        for arg in args[0:]:
            target.write("./")
            target.write(arg)
            target.write(" ")       
    target.write("\n")

    return

def mk_build_all(target, data):
    target.write("CP = cp -rf\n")

    args = []
    if "launch" in data:
        if "cmd_args" in data["launch"][0]:
            args = data["launch"][0]["cmd_args"].split(" ")
            if any("/data" in string for string in args):
                target.write("DATA = ./data\n")

    target.write("\n")

    target.write(".PHONY: all clean cleanall docs emconfig\n")
    target.write("all: check-devices $(EXECUTABLE) $(BINARY_CONTAINERS) emconfig\n")
    target.write("\tmake sd_card\n")
    target.write("\n")
    
    target.write(".PHONY: exe\n")
    target.write("exe: $(EXECUTABLE)\n")
    target.write("\n")
    
    target.write(".PHONY: build\n")
    target.write("build: $(BINARY_CONTAINERS)\n")
    target.write("\n")
    
    counter = 0
    if "containers" in data:
	for con in data["containers"]:
	    if "accelerators" in con:
		for acc in con["accelerators"]:
		    if "kernel_type" in acc:
		    	if acc["kernel_type"] == "RTL":
			    counter = 1
    if counter == 1:
	building_kernel_rtl(target, data)
    else:
    	building_kernel(target, data)
    building_host(target, data)
    return

def mk_check(target, data):
    target.write("check: all\n")
    if "ndevice" in data:
        for board in data["ndevice"]:
            target.write("ifeq ($(findstring ")
	    target.write(board)
	    target.write(", $(DEVICE)), ")
	    target.write(board)
            target.write(")\n")                   
            target.write("$(error Nothing to be done for make)\n")
            target.write("endif\n")
        target.write("\n")
    target.write("ifeq ($(TARGET),$(filter $(TARGET),sw_emu hw_emu))\n")
    target.write("ifeq ($(HOST_ARCH), x86)\n")
    target.write("\t$(CP) $(EMCONFIG_DIR)/emconfig.json .\n") 
    target.write("\tXCL_EMULATION_MODE=$(TARGET) ./$(EXECUTABLE)")
    
    if "launch" in data:	
        if "cmd_args" in data["launch"][0]:
            args = data["launch"][0]["cmd_args"].split(" ")    
            for arg in args[0:]:
                target.write(" ")
                arg = arg.replace('BUILD', '$(BUILD_DIR)')
	        arg = arg.replace('PROJECT', '.')
	        target.write(arg)
    target.write("\nelse\n")
    target.write("\tlaunch_emulator -no-reboot -runtime ocl -t $(TARGET) -sd-card-image _vimage/emulation -device-family $(DEV_FAM)\n")
    target.write("\thead -n -3 _vimage/emulation/sd_card.manifest | tee _vimage/emulation/sd_card.manifest\n")
    target.write("\thead -n -2 _vimage/emulation/init.sh | tee _vimage/emulation/init.sh\n")
    target.write("endif\n")
    target.write("else\n")
    target.write("ifeq ($(HOST_ARCH), x86)\n")
    target.write("\t./$(EXECUTABLE)")
	
    if "launch" in data:
        if "cmd_args" in data["launch"][0]:
            args = data["launch"][0]["cmd_args"].split(" ")    
            for arg in args[0:]:
                target.write(" ")
	        arg = arg.replace('BUILD', '$(BUILD_DIR)')
	        arg = arg.replace('PROJECT', '.')
	        target.write(arg)
    target.write("\nendif\n")
    target.write("endif\n")
    if "targets" in data:
        target.write("ifneq ($(TARGET),$(findstring $(TARGET),")
        args = data["targets"]
        for arg in args:
            target.write(" ")
            target.write(arg)
        target.write("))\n")
        target.write("$(warning WARNING:Application supports only")
        for arg in args:
            target.write(" ")
            target.write(arg)
        target.write(" TARGET. Please use the target for running the application)\n")
        target.write("endif\n")
        target.write("\n")

    if data["name"] != "00 Matrix Multiplication":
        target.write("ifeq ($(HOST_ARCH), x86)\n")
        target.write("\tperf_analyze profile -i profile_summary.csv -f html\n")
        target.write("endif\n")
    target.write("\n")

    target.write("sd_card: $(EXECUTABLE) $(BINARY_CONTAINERS) emconfig\n")
    target.write("ifneq ($(HOST_ARCH), x86)\n")
    target.write("ifeq ($(TARGET),$(filter $(TARGET),sw_emu hw_emu))\n")
    target.write("\t$(CP) $(BINARY_CONTAINERS) .\n")
    target.write("\treadlink -f $(EXECUTABLE) >> _vimage/emulation/sd_card.manifest\n")
    target.write("\treadlink -f xrt.ini >> _vimage/emulation/sd_card.manifest\n")

    target.write("\treadlink -f $(BUILD_DIR)/*.xclbin >> _vimage/emulation/sd_card.manifest\n")
    
    if os.path.exists("data"):
        target.write("\treadlink -f data >> _vimage/emulation/sd_card.manifest\n")

    target.write("\t$(ECHO) ./$(EXEC_CMD_ARGS) >> _vimage/emulation/init.sh\n")
    target.write("\t$(ECHO) \"reboot\" >> _vimage/emulation/init.sh\n")
    target.write("\t$(ABS_COMMON_REPO)/common/utility/sd_card_generation.tcl\n")
    target.write("\tmkfatimg _vimage/emulation/sd_card _vimage/emulation/sd_card.img 500000\n")
    target.write("else\n")
    target.write("\tmkdir -p sd_card\n")
    target.write("\t$(CP) $(B_NAME)/sw/$(XSA)/xrt/image/* $(BUILD_DIR)/*.xclbin $(EXECUTABLE) sd_card/\n")
    target.write("\t$(ECHO) ./$(EXEC_CMD_ARGS) >> sd_card/init.sh\n")
    target.write("endif\n")
    target.write("endif\n")
    target.write("\n")

def run_nimbix(target, data):
    target.write("run_nimbix: all\n")
    if "launch" in data:
        if "cmd_args" in data["launch"][0]:
    	    target.write("\t$(COMMON_REPO)/common/utility/nimbix/run_nimbix.py $(EXECUTABLE) $(CMD_ARGS) $(XSA)\n\n")
    else:
        target.write("\t$(COMMON_REPO)/common/utility/nimbix/run_nimbix.py $(EXECUTABLE) $(XSA)\n\n")	
    
def aws_build(target):
    target.write("aws_build: check-aws_repo $(BINARY_CONTAINERS)\n")
    target.write("\t$(COMMON_REPO)/common/utility/aws/run_aws.py $(BINARY_CONTAINERS)\n\n")

def mk_help(target):
    target.write(".PHONY: help\n")
    target.write("\n")
    target.write("help::\n")
    target.write("\t$(ECHO) \"Makefile Usage:\"\n")
    target.write("\t$(ECHO) \"  make all TARGET=<sw_emu/hw_emu/hw> DEVICE=<FPGA platform> HOST_ARCH=<aarch32/aarch64/x86> SYSROOT=<sysroot_path>\"\n");
    target.write("\t$(ECHO) \"      Command to generate the design for specified Target and Shell.\"\n")
    target.write("\t$(ECHO) \"      By default, HOST_ARCH=x86. HOST_ARCH and SYSROOT is required for SoC shells\"\n")
    target.write("\t$(ECHO) \"\"\n")
    target.write("\t$(ECHO) \"  make clean \"\n");
    target.write("\t$(ECHO) \"      Command to remove the generated non-hardware files.\"\n")
    target.write("\t$(ECHO) \"\"\n")
    target.write("\t$(ECHO) \"  make cleanall\"\n")
    target.write("\t$(ECHO) \"      Command to remove all the generated files.\"\n")
    target.write("\t$(ECHO) \"\"\n")
    target.write("\t$(ECHO) \"  make sd_card TARGET=<sw_emu/hw_emu/hw> DEVICE=<FPGA platform> HOST_ARCH=<aarch32/aarch64/x86> SYSROOT=<sysroot_path>\"\n");
    target.write("\t$(ECHO) \"      Command to prepare sd_card files.\"\n")
    target.write("\t$(ECHO) \"      By default, HOST_ARCH=x86. HOST_ARCH and SYSROOT is required for SoC shells\"\n")
    target.write("\t$(ECHO) \"\"\n")
    target.write("\t$(ECHO) \"  make check TARGET=<sw_emu/hw_emu/hw> DEVICE=<FPGA platform> HOST_ARCH=<aarch32/aarch64/x86> SYSROOT=<sysroot_path>\"\n");
    target.write("\t$(ECHO) \"      Command to run application in emulation.\"\n")
    target.write("\t$(ECHO) \"      By default, HOST_ARCH=x86. HOST_ARCH and SYSROOT is required for SoC shells\"\n")
    target.write("\t$(ECHO) \"\"\n")
    target.write("\t$(ECHO) \"  make build TARGET=<sw_emu/hw_emu/hw> DEVICE=<FPGA platform> HOST_ARCH=<aarch32/aarch64/x86> SYSROOT=<sysroot_path>\"\n");
    target.write("\t$(ECHO) \"      Command to build xclbin application.\"\n")
    target.write("\t$(ECHO) \"      By default, HOST_ARCH=x86. HOST_ARCH and SYSROOT is required for SoC shells\"\n")
    target.write("\t$(ECHO) \"\"\n")
    #target.write("\t$(ECHO) \"  make run_nimbix DEVICE=<FPGA platform>\"\n");
    #target.write("\t$(ECHO) \"      Command to run application on Nimbix Cloud.\"\n")
    #target.write("\t$(ECHO) \"\"\n")
    #target.write("\t$(ECHO) \"  make aws_build DEVICE=<FPGA platform>\"\n");
    #target.write("\t$(ECHO) \"      Command to build AWS xclbin application on AWS Cloud.\"\n")
    #target.write("\t$(ECHO) \"\"\n")
    target.write("\n")

def report_gen(target, data):
    target.write("#+-------------------------------------------------------------------------------\n")
    target.write("# The following parameters are assigned with default values. These parameters can\n")
    target.write("# be overridden through the make command line\n")
    target.write("#+-------------------------------------------------------------------------------\n")
    target.write("\n")

    if "testinfo" in data and "profile" in data["testinfo"] and data["testinfo"]["profile"] == "no":
        pass
    else:
        target.write("PROFILE := no\n")
        target.write("\n")
        target.write("#Generates profile summary report\n")
        target.write("ifeq ($(PROFILE), yes)\n")
        target.write("LDCLFLAGS += --profile_kernel data:all:all:all\n")
        target.write("endif\n")
        target.write("\n")
    
    target.write("DEBUG := no\n")
    target.write("B_TEMP = `$(ABS_COMMON_REPO)/common/utility/parse_platform_list.py $(DEVICE)`\n")
    target.write("\n")
    target.write("#Generates debug summary report\n")
    target.write("ifeq ($(DEBUG), yes)\n")
    target.write("LDCLFLAGS += --dk list_ports\n")
    target.write("endif\n")
    target.write("\n")

def device2xsa_gen(target):
    target.write("#   device2xsa - create a filesystem friendly name from device name\n")
    target.write("#   $(1) - full name of device\n")
    target.write("device2xsa = $(strip $(patsubst %.xpfm, % , $(shell basename $(DEVICE))))\n")
    target.write("\n")

def util_checks(target):
    target.write("#Setting Platform Path\n")
    target.write("ifeq ($(findstring xpfm, $(DEVICE)), xpfm)\n")
    target.write("\tB_NAME = $(shell dirname $(DEVICE))\n")
    target.write("else\n")
    target.write("\tB_NAME = $(B_TEMP)/$(DEVICE)/$(DEVICE).xpfm)\n")
    target.write("endif\n")
    target.write("\n")

    target.write("#Checks for XILINX_VITIS\n")
    target.write("ifndef XILINX_VITIS\n")
    target.write("$(error XILINX_VITIS variable is not set, please set correctly and rerun)\n")
    target.write("endif\n")
    target.write("\n")

    target.write("#Checks for Device Family\n")
    target.write("ifeq ($(HOST_ARCH), aarch32)\n")
    target.write("\tDEV_FAM = 7Series\n")
    target.write("else ifeq ($(HOST_ARCH), aarch64)\n")
    target.write("\tDEV_FAM = Ultrascale\n")
    target.write("endif\n")
    target.write("\n")

    target.write("#Checks for XILINX_XRT\n")
    target.write("check-xrt:\n")
    target.write("ifndef XILINX_XRT\n")
    target.write("\t$(error XILINX_XRT variable is not set, please set correctly and rerun)\n")
    target.write("endif\n")
    target.write("\n")

    target.write("#Checks for SYSROOT\n")
    target.write("ifneq ($(HOST_ARCH), x86)\n")
    target.write("ifndef SYSROOT\n")
    target.write("$(error SYSROOT variable is not set, please set correctly and rerun)\n")
    target.write("endif\n")
    target.write("endif\n")
    target.write("\n")

    target.write("check-devices:\n")
    target.write("ifndef DEVICE\n")
    target.write("\t$(error DEVICE not set. Please set the DEVICE properly and rerun. Run \"make help\" for more details.)\n")
    target.write("endif\n")
    target.write("\n")

    #target.write("check-aws_repo:\n")
    #target.write("ifndef SDACCEL_DIR\n")
    #target.write("\t$(error SDACCEL_DIR not set. Please set it properly and rerun. Run \"make help\" for more details.)\n")
    #target.write("endif\n")
    #target.write("\n")

def clean_util(target):
    target.write("# Cleaning stuff\n")
    target.write("RM = rm -f\n")
    target.write("RMDIR = rm -rf\n")
    target.write("\n")
    target.write("ECHO:= @echo\n")
    target.write("\n")
    
def readme_gen(target):
    target.write("docs: README.md\n")
    target.write("\n")
    target.write("README.md: description.json\n")
    target.write("\t$(ABS_COMMON_REPO)/common/utility/readme_gen/readme_gen.py description.json")
    target.write("\n")   

    
def create_mk(target, data):
    mk_help(target)
    create_params(target,data)
    add_host_flags(target, data)
    add_kernel_flags(target, data)
    add_containers(target, data)
    mk_build_all(target, data)
    mk_check(target, data)
    #run_nimbix(target, data)
    #aws_build(target)
    mk_clean(target,data)
    return 

def create_utils(target, data): 
    report_gen(target, data) 
    util_checks(target)
    device2xsa_gen(target)
    clean_util(target)
    readme_gen(target)
    return

def create_config(data):
    if "containers" in data:
        for con in data["containers"]:
            if "accelerators" in con:
                for acc in con["accelerators"]:
                    if "compute_units" in acc or "num_compute_units" in acc:
                        config_file = 0	
                        for dirs,subdirs,files in os.walk("."):
	                    if con["name"]+".ini" in files:
	                        config_file = 1
			if config_file == 1:	
		            target = open(con["name"]+".ini","a")
		        else:	
                            print "Creating "+con["name"]+".ini file for %s" %data["name"]
                            target = open(con["name"]+".ini","w")
                            target.write("[connectivity]\n")
                    if "compute_units" in acc:
                        for com in acc["compute_units"]:
                            if "arguments" in com:
                                for arg in com["arguments"]:
                                    target.write("sp="+acc["name"]+"_"+str(acc["compute_units"].index(com)+1)+"."+arg["name"]+":"+arg["memory"]+"\n")
                            if "slr" in com:
                                target.write("slr="+acc["name"]+"_"+str(acc["compute_units"].index(com)+1)+":"+com["slr"]+"\n")
                    if "num_compute_units" in acc:
				target.write("nk="+acc["name"]+":"+acc["num_compute_units"]+"\n")
    return

script, desc_file = argv
desc = open(desc_file, 'r')
data = json.load(desc)
desc.close()

if "match_ini" in data and data["match_ini"] == "false":
    print "Error:: xrt.ini File Manually Edited:: Auto-file Generator Failed"
    err = False
else:
    print "Generating xrt.ini file for %s" %data["name"]
    target = open("xrt.ini","w+")
    profile_report(target)

if "containers" in data:
        config_flag = 0
	for con in data["containers"]:
		for dirs,subdirs,files in os.walk("."):
			if con["name"]+".ini" in files:
				config_flag = 1
	if not config_flag:
            create_config(data)	

if "match_makefile" in data and data["match_makefile"] == "false":
    print "Error:: Makefile Manually Edited:: AutoMakefile Generator Failed"
else:
    print "Generating Auto-Makefile for %s" %data["name"]
    target = open("Makefile", "w")
    create_mk(target, data)
    print "Generating utils.mk file for %s" %data["name"]
    target = open("utils.mk", "w+")
    create_utils(target, data)

target.close


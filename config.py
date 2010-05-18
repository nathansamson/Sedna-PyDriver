##############################################################################
## File:  config.py
##
## Copyright (C) 2010, Apache License 2.0 
## The Institute for System Programming of the Russian Academy of Sciences
## 
## Setup configuration file. 
##
## SEDNA_BIN_PATH - path to Sedna binary tree
##                  Setup expects to find {SEDNA_BIN_PATH}/driver/c
##                  folder with headers and libs in it.
##
##              e.g. SEDNA_BIN_PATH="C:\\sedna" (Windows)
##                   SEDNA_BIN_PATH="/home/user/sedna" (*Nix)
## SEDNA_SRC_PATH - path to Sedna source tree
##                  This allows to build the driver from scratch
##                  (ignored if SEDNA_BIN_PATH contains all the necessary
##                   components)
##
##              e.g. SEDNA_SRC_PATH="C:\\sedna" (Windows)
##                   SEDNA_SRC_PATH="/home/user/sedna" (*Nix)
##############################################################################

SEDNA_BIN_PATH=""
SEDNA_SRC_PATH=""

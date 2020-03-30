CC=g++
SRC=sir_model.cpp
BIN=sir_model
FLAGS=-O2 -std=c++14 -Wall -Werror
INCLUDES=-I/usr/include/eigen3
LIBS=-lgflags -lglog -lceres

all:
	$(CC) -o $(BIN) $(FLAGS) $(INCLUDES) $(SRC) $(LIBS)

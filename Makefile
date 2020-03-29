CC=g++
SRC=sir_model.cpp
BIN=sir_model
FLAGS=-O2 -std=c++14 -Wall -Werror
LIBS=-lgflags -lglog

all:
	$(CC) -o $(BIN) $(FLAGS) $(SRC) $(LIBS)

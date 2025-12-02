NAME = multithreaded_imfant
CC = /opt/homebrew/bin/g++-14
LIBRARIES = iMFAnt.cpp
HEADERS = iMFAnt.hpp
UNAME_S := $(shell uname -s)



all: $(NAME)

$(NAME): $(HEADERS) $(LIBRARIES) $(NAME).cpp

	$(CC) -fopenmp -o $@ $(NAME).cpp $(LIBRARIES) -O3 -DREPS=1 -D_Alignof=__alignof__

clean:
	rm -f $(NAME)

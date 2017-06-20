#! /usr/bin/env python

## Copyright (c) 2015, FlySorter, LLC
## Code that combines robotutil and imgprocess to find flies and execute commands 
## getAllFlies takes as primary input the location and size of a maze and of a fly pad
## and automatically takes all flys in the fly pad area and moves them to the maze location
## TODO: hard code/use machine vision to specify actual locations of mazes

## By: Will Long
## MRU: Nov 29 2015

import cv2
import numpy as np
import time
import random

import robotutil
import imgprocess

## Some defaults & settings

        
#### BEGIN PGM ####

robot = robotutil.santaFe("FlySorter.cfg")

if robot.isInitialized == False:
    print "Initialization error."
    exit()
else:
    print "Robot initialized."

robot.home()

# --------- Start Test Code -------

#move robot to hard coded fly pad location
reference = (390, 410)
PPMM = 28
padLocation = (110, 110, 10, 0, 0)     #location of top left hand corner of pad
padSize = (50, 50)                    #size of the pad in x, y
mazeLocation = (500, 100, 10, 0, 0)
imageSize = (1900/PPMM, 1900/PPMM)      #(1900, 1900) in pixels

def generateMazeLocs():
    mazeLocs = []
    oddMaze1 = (304, 244)
    evenMaze1 = (290, 204)

    for row in range(5):        # camera can't seem to capture farthest row
        mazeRow = []
        for col in range(9):
            mazeRow.append((oddMaze1[0] - col * 30, oddMaze1[1] - row * 56))
        mazeLocs.append(mazeRow)

    return mazeLocs

def getAllFlies(robot, padLocation, padSize, imageSize, mazeLocation):
    
    duration = 2
    plateBool = 1
    a = imgprocess.imageProcess()
    
    #how many images do we need to take?
    xSweeps = padSize[0]/imageSize[0] + 1
    ySweeps = padSize[1]/imageSize[1] + 1
    
    #all the different locations we will need to image
    camXY = []
    for x in range(xSweeps+1):
        for y in range(ySweeps+1):
            camXY.append((x * padSize[0]/xSweeps, y * padSize[1]/ySweeps))
    
    for (x,y) in camXY:
        
        robot.moveTo((padLocation[0] + x, padLocation[1] + y, padLocation[2], padLocation[3], padLocation[4]))
        print "Imaging:", (x,y)
        img = robot.captureImage()
        cv2.imwrite('actual.bmp', img)
        targets = a.execute(img, reference)

        for (x,y) in targets:
            pt = (reference[0] + x, reference[1] + y, padLocation[2], padLocation[3], padLocation[4])
            print "Getting Fly at point:", pt
            robot.moveTo(pt)
            robot.dipAndGetFly(pt, duration, plateBool)

            robot.moveTo(mazeLocation)      #drop them all off at a single location for now
            robot.depositInMaze(mazeLocation, duration)

# getAllFlies(robot, padLocation, padSize, imageSize, mazeLocation)  

def executeLids(robot): 
    mazes = generateMazeLocs() 

    numCorrect = 0
    numMazes = 6 * len(mazes[0])

    a = imgprocess.imageProcess()

    for row in range(2):
        for maze in mazes[row]:
            img = cv2.resize(robot.captureImage(), ( 864, 648 ))
            cv2.imwrite('temp_img.png', img)
            targets = a.findOpening('temp_img.png')

            counter = 0
            while not targets or not len(targets) == 1:
                
                if counter > 10:
                    print "Problem unsolved after 10 attempts"
                    robot.release()
                
                print "Problem finding Opening. Trying again..."
                
                # Jiggle robot
                xPos, yPos, z0Pos, z1Pos, z2Pos = robot.getCurrentPosition()
                dx = 10 * random.random()
                dy = 10 * random.random()
                robot.moveTo(xPos + dx, yPos + dy, z0Pos, z1Pos, z2Pos)
                robot.moveTo(xPos - dx, yPos - dy, z0Pos, z1Pos, z2Pos)

                img = cv2.resize(robot.captureImage(), ( 864, 648 ))
                cv2.imwrite('temp_img.png', img)
                targets = a.findOpening('temp_img.png')

                counter += 1

            result = input("Is this target correct?")
            print result

            if result == "y":
                
                numCorrect = numCorrect + 1
                # cv2.destroyAllWindows()
            # else:
                # cv2.destroyAllWindows()

            robot.moveTo((maze[0], maze[1], 0, 30, 0))

    print str(numCorrect) + " correct out of " + str(numMazes)
    robot.release()
[![Build Status](https://travis-ci.org/bfellman/cortex.svg?branch=master)](https://travis-ci.org/bfellman/cortex)
[![codecov](https://codecov.io/gh/bfellman/cortex/branch/master/graph/badge.svg)](https://codecov.io/gh/bfellman/cortex)
# Cortex Thought Processing System

## Intro
The Cortex system enables user to store snapshots of their thoughts in remote server, for further processing and storage.
The system simulates a [client](#client) uploading data (as the hardware device doesn't exist yet), and implements a remote [server](#server) communicating with a variety of [parsers](#parsers) through a [message queue](#message-queue)
Parsed results are [stored to a database](#saver), exposed by a [web API](#web-api) and can be accessed by a [CLI](#cli)   
[system_arch_images](https://github.com/bfellman/cortex/blob/master/cortex_arch.png)

This is the final project in [Advanced System Design](https://advanced-system-design.com/) course, given in Tel-Aviv University on  winter 2019-2020

## Setup
First Clone the repo:
```bash
$ git clone https://github.com/bfellman/cortex.git
```
Then install and activate:
```bash
$ cd cortex
$ ./scripts/install.sh
… 
$ source .env/bin/activate
[cortex] $ 
```
### Requirements
- `docker` for running message queue and database
- `python3.8`, `virtualenv` and `pip` 

## System Components
### Client
The client expect to receive a sample protobuf file, where the first message is the User information, and the rest are snapshots. 

### Server

### Message Queue

### Parsers

### Saver

### Web API

## CLI
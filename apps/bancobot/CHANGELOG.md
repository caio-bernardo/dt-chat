# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] -- 2026-01-19

## Added
- `TimingMetadata` for message creation, containing info about user's message.

### Modified
- `BancoAgent` inherits from `chatbot` library.
- `BancoAgent` saves checkpoints in sqlite database
- `Message` caries now metadata about the timinig simulation. Both AI and Human messages carry the metadata, AI messages have the simulated timestamp of the incoming human message.
- Add checkpoint saver as a dependecy for the agent, so it less coupled.

### Removed
- throw away tests since everything broke. (terrible practice I know)

## [0.2.0] -- 2025-12-13

### Added
- `bancobot` package with FastAPI aplication, SQLModel ORM and SQLite database, plus Langchain agent
- `embender` script to create vector store from documents
- Full test suite for `bancobot`

## [0.1.0] -- 2025-11-25

### Added
- project setup, including pyproject.toml
- README basics

### Changed
- migrate to MIT License

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),

## [Unreleased]

### Added
- **Phase 3: Expense Classification System**
  - Classification rule models with regex patterns and priorities
  - YAML-based rule storage
  - Case-insensitive pattern matching engine
  - Transaction classifier for batch processing
  - Classification applicator to update account codes
  - Rule learning system to extract patterns from user classifications
  - Workflow orchestrator with acceptance decisions (ACCEPTED, REJECTED, MANUAL, PENDING)
  - Storage integration with Phase 2 JSONL transaction store
  - Auto-learning rules from accepted/rejected classifications
  - Complete documentation and usage guide

- **Storage Enhancements**
  - `update_transaction()` function to update existing transactions in JSONL files

## [0.1.0] - 2025-05-16

### Fixed

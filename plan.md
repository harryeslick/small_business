# Small_business

this package is designed to be a simple tool for assisting with managment of invoiving and account management for a sole trader small bussiness in australia.
The package is designed for a simple sole trader small bussiness, with low account complexity. The software should be easy to manage and make bussiness managment simpler, not more complex.

## Design philosophy

The package should be simple and light weight and portable. the software is designed to run locally on a single machine. 
All datafiles should be stored as plain text formats. csv for data, configuration as YAML or json. 
The software should be stateless, with account state stored in plain text and loaded at startup. 

package should be written in python, using a terminal TUI user interface 


THe following features are required.

## Acounting Features

- Read in account statements from .csv exported from one or more bank accounts.
- Perform standard accounting best practice management, such as double entry accounting, item classificaiton, P&L reports, Business Activity Statements etc. 

### Expense tracking.

- expenses from all bank accounts tracked should be classified into a set of predetermined classifications/accounts, eg.
    - travel:
        - flights
        - vehicle
    - materials:
        - stationary
        -
    utilities:
        - internet
        - phone
    accounts should be classied in a two depth heirachy. classes should be predetermined and stored as user modifiable JSON file. Create a list of standard accounts to use as default setup.
- expense classification should occur semi-autonomsly, with a set of rules built and saved from previous entries. All software generated classificatiobs must be accepted by the user (or replaced) before being used.
- expense classification should be intellegenetly build from previous user accpted records and user specified rules, which are stored in a separate file. 

- all expenses should be reconciled with a reciept.
- user will add reciepts to each line item, software should save these in a standard folder structure, and rename each file and link to the relevant line item.


### Income management

- preparation of quotes and invoicing from an input form and exporting to microsoft word using Jinja2 templating.
- use an internal job management workflow progressing from quotes > jobs (accepted quote) > invoice.
- allow for modification of existing quotes and invoices using versioning.
- tracking of income agaist quotes and invoices. ensure all jobs get invoiced, and all invoices are paid. 
- interface with calender via .ics to ensure important dates, such as quoted events are recorded in the local calender system.

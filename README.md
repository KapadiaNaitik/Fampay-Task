# Fampay Task

This is the task assigned for the backend intern position at Fampay

## Features

- **Dashboard:** A dashboard to view the stored videos with sorting options.

- **Query Updation:** There is an input field to update the search query instead of the one used in .env.

- **Support for multiple API Keys:** Multiple API Keys are allowed and they are used one after the another sort of like a simple round robin algorithm with key quantum of one request .

## Setup

Follow these steps to set up the project locally:

1. Clone the repository:

```bash
git clone https://github.com/KapadiaNaitik/Fampay-Task.git
```

2. Navigate to the project directory:

```bash
cd Fampay-Task
```

3. Install the requirements:

```bash
pip install -r requirements.txt
```

4. Setup env file

5. Initialize the database

```bash
flask initdb
```

## Usage

First, run the development server:

```bash
python app.py
```

Open [http://localhost:5000/dashboard](http://localhost:5000/dashboard) with your browser to see the result.

This will start the development server and open the app in your default web browser.

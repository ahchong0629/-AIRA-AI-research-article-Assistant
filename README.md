# AI research article assistant

Version 1: 15 May 2026, 
Author: ahchong0629

Short in time to skim through several research paper before conference or discussion? Here is your assistant to help you!

The AI research article assistant (AIRA) provides you the summary of the article by simply uploading the PDF file and it will summarize the motivation, procedure, results as well as the key figure of the article within minutes! It also creates a text file that save locally in your computer.

<div align="center">
  <img width="815" height="409" alt="Screenshot 2026-05-15 at 11 43 29" src="https://github.com/user-attachments/assets/3359fcd2-006a-46e7-bcc5-99bbfb776dab" />
</div>

## Features

Simply upload the PDF file of the article and AIRA will provide the following:

1. Summarizing motivation, method, results and potential open question

2. Identifying and analyzing the most important figure

3. (More to come!)



## Tech Stack & Prerequisites 

1. AIRA is supported by using python (for coding), OpenAI GPT-4o (for the brain), Gradio (for the interactive interface), PymuPDF (for extracting the text).

2. Please update your own OpenAI API key (set in ".env" file, format: 'OPENAI_API_KEY=sk-xxxxx')

(If you need help to know where to find the OpenAI API key, please visit: https://help.openai.com/en/articles/4936850-where-do-i-find-my-openai-api-key)



## Installation and Usage
Please install 
```pip install -r requirements.txt``` and if you are using macOS/Linux, simply just run ```python3 main.py``` . It should provide you the corresponding local URL to start AIRA. 

It should show something like "* Running on local URL:  http://127.0.0.1:7919"

## Note
Please note that the brain might make mistake, please verify the given information beforehands.

## Author 
Wei Chuang Lee· [@ahchong0629] (https://github.com/ahchong0629)


## License 
Copyright (c) 2026 Wei chuang Lee

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to conditions.



from flask import Flask, render_template_string, request
import spacy
from spacy.lang.en.stop_words import STOP_WORDS
from string import punctuation
from heapq import nlargest

app = Flask(__name__)


def summarizer(rawdocs):
    
    custom_stopwords = ['your', 'specific', 'domain', 'words']
    stopwords = list(spacy.lang.en.stop_words.STOP_WORDS) + custom_stopwords  
    nlp = spacy.load('en_core_web_sm')
    doc = nlp(rawdocs)

    # Word frequency  
    word_freq = {}
    for word in doc:
        if word.text.lower() not in stopwords and not word.is_punct and not word.is_space:  
            word_freq[word.text.lower()] = word_freq.get(word.text.lower(), 0) + 1

    
    max_freq = max(word_freq.values(), default=1)
    for word in word_freq:
        word_freq[word] = word_freq[word] / max_freq

    # Sentence scoring 
    sent_tokens = [sent for sent in doc.sents]
    sent_scores = {}
    for i, sent in enumerate(sent_tokens):
        for word in sent:
            if word.text.lower() in word_freq:
                sent_scores[sent] = sent_scores.get(sent, 0) + word_freq[word.text.lower()]
        # Positional weight
        sent_scores[sent] += (len(sent_tokens) - i) / len(sent_tokens)

    # Select top sentences 
    select_len = max(1, int(len(sent_tokens) * 0.3))  #at least one sentence
    summary = nlargest(select_len, sent_scores, key=sent_scores.get)

    
    final_summary = [sent.text for sent in summary]
    summary_text = ' '.join(final_summary)

    
    summary_doc = nlp(summary_text)
    return summary_text, len(rawdocs.split()), len([token.text for token in summary_doc if not token.is_space])

# HTML Templates
index_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Text Summarization</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.0.0/dist/css/bootstrap.min.css" />
    <style>
        .jumbotron {
            background-color: orange;
        }
        .heading {
            font-weight: bold;
            text-align: center;
        }
        .lead {
            text-align: center;
        }
        .submitbtn {
            margin-top: 10px;
            display: block;
            width: 100%;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="jumbotron jumbotron-fluid">
            <div class="container">
                <h1 class="display-4 heading">Text Summarization</h1>
                <p class="lead">Retrieve the best summary for your text</p>
            </div>
        </div>
    </div>

    <div class="container">
        <form action="/analyze" method="POST">
            <div class="form-group">
                <label for="rawtext">Enter Text:</label>
                <textarea 
                    name="rawtext" 
                    id="rawtext" 
                    class="form-control" 
                    rows="8" 
                    placeholder="Enter your raw text here..."
                    required></textarea>
            </div>
            <button class="btn btn-primary submitbtn" type="submit">Submit</button>
        </form>
    </div>
</body>
</html>
"""

summary_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Summary</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.0.0/dist/css/bootstrap.min.css" />
    <style>
        .jumbotron {
            background-color: orange;
        }
        .original_title {
            background-color: orangered;
            font-size: 20px;
            font-weight: bold;
            padding: 5px;
            text-align: center;
        }
        .summary_title {
            background-color: greenyellow;
            font-size: 20px;
            font-weight: bold;
            padding: 5px;
            text-align: center;
        }
        .originalTxt {
            background-color: orangered;
            padding: 20px;
            border-radius: 5px;
            color: white;
        }
        .summaryTxt {
            background-color: greenyellow;
            padding: 20px;
            border-radius: 5px;
            color: black
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="jumbotron jumbotron-fluid">
            <div class="container">
                <h1 class="display-4 heading">Text Summarization</h1>
                <p class="lead">Retrieve the best summary for the text</p>
            </div>
        </div>
    </div>

    <div class="container">
        <div class="row">
            <div class="col-sm-6">
                <h3 class="original_title">Original Text</h3>
                <p class="originalTxt">{{ original_txt }}</p>
                <button class="btn btn-danger">Words: {{ len_orig_txt }}</button>
            </div>
            <div class="col-sm-6">
                <h3 class="summary_title">Summary</h3>
                <p class="summaryTxt">{{ summary }}</p>
                <button class="btn btn-success">Words: {{ len_summary }}</button>
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(index_html)

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        # Fetch text 
        rawtext = request.form['rawtext']
        summary, len_orig_text, len_summary = summarizer(rawtext)
        return render_template_string(
            summary_html,
            summary=summary,
            original_txt=rawtext,
            len_orig_txt=len_orig_text,
            len_summary=len_summary
        )
    except Exception as e:
        return f"An error occurred: {str(e)}"

if __name__ == "__main__":
    app.run(debug=True)

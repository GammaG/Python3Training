from flask import Flask, render_template, request, redirect, escape
from main.vsearch import search4letters
from main.DatabaseConnection import DatabaseConnection

app = Flask(__name__)

log_path = 'logs/log.txt'
logContent = []
titles = ('Form Data', 'Remote_addr', 'User_agent', 'Results')

dbconfig = {'host': '127.0.0.1',
            'user': 'vsearch',
            'password': 'vsearchpasswd',
            'database': 'vsearchlogdb'}
_SQL_insert_statement = """insert into log (phrase, letters, ip, browser_string, results) values (%s, %s, %s, %s, %s)"""
_SQL_fetchall_statement = """select phrase, letters, ip, browser_string, results from log"""


@app.route('/')
@app.route('/entry')
def entry_page() -> 'html':
    return render_template('entry.html', the_title='Welcome to search4letters on the web!')


@app.route('/search4', methods=['POST'])
def do_search() -> 'html':
    phrase: str = request.form['phrase']
    letters: str = request.form['letters']
    results: str = str(search4letters(phrase, letters))
    log_request(request, results)
    save_log_in_database(request, results)
    return render_template('results.html', the_phrase=phrase, the_letters=letters, the_title="Your results:",
                           the_results=results)


@app.route('/search4', methods=['GET'])
def init() -> '302':
    return redirect('/entry')


@app.route('/viewlog', methods=['GET'])
def showlog() -> 'html':
    with open(log_path) as log:
        for line in log:
            logContent.append([])
            for item in line.split('|'):
                logContent[-1].append(escape(item))
    return render_template('viewlog.html', the_title='View Log', the_row_titles=titles, the_data=logContent)


@app.route('/viewlogDB', methods=['GET'])
def showlogFromDB() -> 'html':
    with DatabaseConnection(dbconfig) as cursor:
        cursor.execute(_SQL_fetchall_statement)
        logContent = createLogList(cursor.fetchall())
    return render_template('viewlog.html', the_title='View Log', the_row_titles=titles, the_data=logContent)


def log_request(req: 'flask_request', res: str) -> None:
    with open(log_path, 'a') as log:
        print(req.form, req.remote_addr, req.user_agent, res,
              file=log, sep='|')


def save_log_in_database(req: 'flask_request', res: str) -> None:
    """Use @DatabaseConnection Class to open a connection and insert values"""
    with DatabaseConnection(dbconfig) as cursor:
        cursor.execute(_SQL_insert_statement,
                       (req.form['phrase'], req.form['letters'], req.remote_addr, req.user_agent.browser, res))


def createLogList(list: []) -> []:
    logContent = []
    for entry in list:
        logContent.append([])
        for item in entry:
            logContent[-1].append(escape(item))
    return logContent


if __name__ == '__main__':
    app.run(debug=True)

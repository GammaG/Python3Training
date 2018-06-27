from flask import Flask, render_template, request, redirect, escape, session, copy_current_request_context
from main.vsearch import search4letters
from main.DatabaseConnection import DatabaseConnection
from resources.webapp.checker import check_logged_in
from threading import Thread

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
app.secret_key = 'YouWillNeverGuessMySecretKey'


@app.route('/')
@app.route('/entry')
def entry_page() -> 'html':
    return render_template('entry.html', the_title='Welcome to search4letters on the web!')


@app.route('/search4', methods=['POST'])
def do_search() -> 'html':
    """copy_current_request_context makes sure that the flask context still exists if the Threads need it,
     to make it working the log functions have to be in here then - ugly so I changed to dictionary"""

    phrase: str = request.form['phrase']
    letters: str = request.form['letters']
    results: str = str(search4letters(phrase, letters))
    elementes = {"phrase": phrase, "letters": letters, "results": results, "remote_addr": request.remote_addr,
                 "user_agent": request.user_agent.browser}
    try:
        Thread(target=log_request, kwargs=elementes).start()
        Thread(target=save_log_in_database, kwargs=elementes).start()
    except Exception as e:
        print("There was problem while logging: " + str(e))
    return render_template('results.html', the_phrase=phrase, the_letters=letters, the_title="Your results:",
                           the_results=results)


@app.route('/search4', methods=['GET'])
def init() -> '302':
    return redirect('/entry')


@app.route('/viewlog', methods=['GET'])
@check_logged_in
def showlog() -> 'html':
    try:
        with open(log_path) as log:
            for line in log:
                logContent.append([])
                for item in line.split('|'):
                    logContent[-1].append(escape(item))
        return render_template('viewlog.html', the_title='View Log', the_row_titles=titles, the_data=logContent)
    except FileNotFoundError:
        print('The data file is missing.')
    except PermissionError:
        print('The file writing wasn\'t allowed.')
    except Exception as e:
        print('An other error occured: ' + str(e))


@app.route('/viewlogDB', methods=['GET'])
@check_logged_in
def showlogFromDB() -> 'html':
    try:
        with DatabaseConnection(dbconfig) as cursor:
            cursor.execute(_SQL_fetchall_statement)
            logContent = createLogList(cursor.fetchall())
        return render_template('viewlog.html', the_title='View Log', the_row_titles=titles, the_data=logContent)
    except:
        return '<h1>The database is not available please try later again.</h1>'


def log_request(phrase, letters, remote_addr, user_agent, results) -> None:
    try:
        with open(log_path, 'a') as log:
            print("Phase: " + phrase + "; Letters:" + "letters", remote_addr, user_agent,
                  results, file=log, sep='|')
    except FileNotFoundError:
        print('The data file is missing.')
    except PermissionError:
        print('The file writing wasn\'t allowed.')
    except Exception as e:
        # except: is the default one
        print('An other error occured: ' + str(e))


def save_log_in_database(phrase, letters, remote_addr, user_agent, results) -> None:
    """Use @DatabaseConnection Class to open a connection and insert values"""
    with DatabaseConnection(dbconfig) as cursor:
        cursor.execute(_SQL_insert_statement, (phrase, letters, remote_addr, user_agent, results))


def createLogList(list: []) -> []:
    logContent = []
    for entry in list:
        logContent.append([])
        for item in entry:
            logContent[-1].append(escape(item))
    return logContent


@app.route('/login')
def do_login() -> str:
    session['logged_in'] = True
    return 'You are now logged in.'


@app.route('/logout')
def do_logout() -> str:
    session.pop('logged_in')
    return 'You are now logged out.'


if __name__ == '__main__':
    app.run(debug=True)

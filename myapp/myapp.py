from crypt import methods
from flask import Flask, request, render_template, jsonify,session,redirect,url_for
import psycopg2
import psycopg2.extras
import json
import hashlib
from datetime import timedelta


connection = psycopg2.connect("host=localhost dbname=s2022054 user=s2022054 password=QWbFwLfQ")

app = Flask(__name__)
#この鍵はなんでも良く、乱数で生成する。このままでもいい
app.config['SECRET_KEY'] = b'PfnlrpCBaLCFKt39'
#セッションは30日残る設定
app.permanent_session_lifetime = timedelta(days=30)

#強制的にhttpsへリダイレクト
@app.before_request
def before_request():
    if not request.is_secure:
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url)
    

@app.route("/dates")
def dates():
    cur = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("select date(pdate),count(cid) from pychat group by \
    date(pdate) order by date(pdate);")
    res = cur.fetchall()
    dict_res = []
    for row in res:
        dict_res.append(dict(row))
    return jsonify(dict_res)
    cur.close()
    
@app.route('/date/<pdate>')
def date(pdate):
    cur = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("select cid,uname,message from pychat where \
    date(pdate)='%s';" % pdate)
    res = cur.fetchall()
    dict_res = []
    for row in res:
        dict_res.append(dict(row))
    return jsonify(dict_res)
    cur.close()
    
@app.route('/home')
def home():
    if "uid" in session and session["uid"]>0 and \
      "uname" in session and len(session["uname"])>0:
        uid=session["uid"]
        uname=session["uname"]
        return render_template("home.html",title="my page",uid=uid,uname=uname)
    else:
        return render_template("home.html")

@app.route('/games', methods=['GET', 'POST'])
def games():
    try:
        if request.method == 'POST' \
        and "uname" in request.form and "message" in request.form \
        and len(request.form['uname'])>0 and len(request.form['message'])>0:
            uname=request.form['uname']
            message=request.form['message']
            cur = connection.cursor()
            cur.execute("insert into pychat(uname,message,pdate) \
            values('%s','%s',current_timestamp);" % (uname, message))
            connection.commit()
            cur.close()
    except Exception as e:
        return str(e)
    
    cur = connection.cursor()
    cur.execute("select cid,uname,message,pdate from pychat order by cid asc;")
    chat = cur.fetchall()
    return render_template('games.html', title='flask chat', chat=chat)

@app.route('/details', methods=['GET', 'POST'])
def details():
    contents = request.args.get('id')
    
    cur1 = connection.cursor()
    cur1.execute("select name, url from mytable where national = %s ;", (contents,))
    mn = cur1.fetchall()
    cur1.close()
    
    cur2 = connection.cursor()
    cur2.execute("select name, Uname, club, url from player where national = %s and Position  = 'GK' order by Uname asc;", (contents,))
    gk = cur2.fetchall()
    cur2.close()
    
    cur3 = connection.cursor()
    cur3.execute("select name, Uname, club, url from player where national = %s and Position  = 'DF';", (contents,))
    df = cur3.fetchall()
    cur3.close()
    
    cur4 = connection.cursor()
    cur4.execute("select name, Uname, club, url from player where national = %s and Position  = 'MF';", (contents,))
    mf = cur4.fetchall()
    cur4.close()
    
    cur5 = connection.cursor()
    cur5.execute("select name, Uname, club, url from player where national = %s and Position  = 'FW';", (contents,))
    fw = cur5.fetchall()
    cur5.close()
    
    return render_template('details.html' ,contents=contents, mn=mn, gk=gk, df=df, mf=mf, fw=fw)

@app.route('/countries')
def countries():
    return render_template('countries.html')

@app.route('/login', methods=['GET'])
def login():
    return render_template("login.html", title="login form")

@app.route('/regist', methods=['GET'])
def regist():
    return render_template("regist.html", title="regist form")

@app.route('/logingin', methods=['POST','GET'])
def logingin():
    error = None
    if request.method == 'POST' \
        and "emf" in request.form and "pwf" in request.form \
        and len(request.form['emf'])>0 and len(request.form['pwf'])>0:
        emf=request.form['emf']
        pwf=request.form['pwf']
        cur = connection.cursor()
        cur.execute("select uid,pw,uname from flskauth where email='%s';" % (emf))
        res = cur.fetchone()
        cur.close()
        cpw=hashlib.sha512(pwf.encode("utf-8")).hexdigest()
        if cpw==res[1]:
            session["uid"]=res[0]
            session["uname"]=res[2]
            return redirect(url_for('home',uname=res[0]))
        else:
            title='login form'
            return render_template('login.html', error=error,title=title)

    title='login form'
    return render_template('login.html', error=error,title=title)



@app.route('/registing', methods=['POST'])
def registing():
    msg=list()
    aflag=0;
    if request.method == 'POST' \
        and "unf" in request.form and "emf" in request.form \
        and "unf" in request.form and "emf" in request.form \
        and "pwf1" in request.form and "pwf2" in request.form \
        and len(request.form['unf'])>0 and len(request.form['emf'])>0 \
        and len(request.form['unf'])>0 and len(request.form['emf'])>0 \
        and len(request.form['pwf1'])>0 and len(request.form['pwf2'])>0:
        unf=request.form['unf']
        emf=request.form['emf']
        pwf1=request.form['pwf1']
        pwf2=request.form['pwf2']
        cur = connection.cursor()
        cur.execute("select count(uid) from flskauth where email='%s';" % (emf))
        res = cur.fetchone()
        cur.close()
        if res[0]>0:
            msg=msg+["このアドレスは既に登録されています。"]
        elif pwf1 != pwf2:
            msg=msg+["パスワードが一致しませんでした。"]
        else:
            cur = connection.cursor()
            epw=hashlib.sha512(pwf1.encode("utf-8")).hexdigest()
            cur.execute("insert into flskauth(uname,email,pw) \
                values('%s','%s','%s');" % (unf, emf,epw))
            connection.commit()
            cur.close()
            msg=msg+["登録完了しました。"]
            aflag=1;
    else:
        msg=msg+["フォームはすべて必須項目です。"]

    return render_template("registing.html", title="registing an user", message=msg, aflag=aflag)



@app.route('/logout')
def logout():
    session.pop("uid", None)
    session.pop("uname", None)
    return redirect("./home")
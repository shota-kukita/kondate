import logging
from flask import Flask, request, render_template, redirect, url_for
import MySQLdb
import datetime
from dotenv import load_dotenv
import os

# DB接続。load_dotenv()で.envファイルの中身を環境変数に反映する。os.getenv()で環境変数を参照する。
load_dotenv()
db_setting = {
    "host": os.getenv('DB_HOSTNAME'),
    "user": os.getenv('DB_USERNAME'),
    "passwd": os.getenv('DB_USERPASS'),
    "db": os.getenv('DATABASE'),
    "charset": "utf8mb4"
}
# flaskとlogの設定
app = Flask(__name__)
logging.basicConfig(format="%(asctime)s [%(levelname)s] %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


# TODO
# food名、seasoning名、栄養素名に単位を含める。例：「豚バラ肉(g)」
# 「"{}".format(name)」 を書き換える。「f"{name}"」
# 関数名をRESTっぽくする。recipeの操作を行うときは"/recipe"で行い、methodがGET, POST, PUT, DELETEで分岐させる。
# 食材を登録する。
# テーブルの列名を順番通りに取得する。


### 以下、関数 ####

def empty_func():
    pass

# 引数のSELECT文を実行し、結果を配列で返す。    
def sql_select_executor_array(query):
    data = []
    try:
        db_conn = MySQLdb.connect(**db_setting)
        try:
            cursor = db_conn.cursor()
            cursor.execute(query)
            data = cursor.fetchall()
        finally:
            db_conn.close()
    except Exception as err:
        logger.error("%s %s", type(err), err)
    return data

# 引数のSELECT文を実行し、結果をhtmlで返す（表形式）。
def sql_select_executor(query):
    data = []
    html_table = "<tr>"
    data = sql_select_executor_array(query)
    for record in data:
        for field in record:
            html_table = html_table + f"<td>{field}</td>"
        html_table = html_table + "</tr>"
    return html_table

# 引数のSQL文(INSERT, UPDATE, DELETE)を実行する。
def sql_notselect_executor(query):
    try:
        db_conn = MySQLdb.connect(**db_setting)
        try:
            cursor = db_conn.cursor()
            cursor.execute(query)
            cursor.close()
            db_conn.commit()
        finally:
            db_conn.close()
    except Exception as err:
        logger.error("%s %s", type(err), err)
    return

# 引数のテーブル名に対する列名を取得し、配列で返す。
def get_array_col_name(table_name):
    # SQLでテーブルの列名を取得する。
    sql_col_name = f"select column_name from information_schema.columns where table_name='{table_name}'"
    col_name = sql_select_executor_array(sql_col_name)
    return col_name

# 開発用。列名をhtmlで取得する。
def get_html_col_name(table_name):
    col_name = []
    html_table = "<tr>"
    sql_col_name = f"select column_name from information_schema.columns where table_name='{table_name}'"    # テーブルの列名を取得するSQL。
    col_name = sql_select_executor_array(sql_col_name)  # テーブルの列名を配列で取得する。
    for record in col_name: # 配列をhtmlの表にする。sql_select_executor()でいきなりhtmlにすると列名が縦並びになる（複数レコードのため）。
        for field in record:
            html_table = html_table + "<td>{}</td>".format(field)
    html_table = html_table + "</tr>"
    return html_table

# 開発用。テーブル全体を表示するhtml。
def get_html_show_table(table_name):
    sql_show_table = f"select * from {table_name}"  # テーブル全体を表示するSQL。　
    html_table = sql_select_executor(sql_show_table)    # SQLを実行。
    html_col_name = get_html_col_name(table_name)       # テーブルの列名を取得する。
    html_show_table = "<table>" + html_col_name + html_table + "</table>"    # テーブルの全体をhtmlの表にする。
    return html_show_table

# 開発用。全テーブル名を配列で取得する。
def get_array_table_name():
    sql_table_name = "select table_name from INFORMATION_SCHEMA.TABLES where TABLE_SCHEMA='kondate_db'"
    array_table_name = []
    array_table_name = sql_select_executor_array(sql_table_name)
    return array_table_name

# 開発用。レコード登録用のテキストボックスを表示するhtmlを作成する。
def get_html_regist_textbox(table_name):
    #table_nameを利用して、get_all_col_name()から列名を取得する。
    col_name = get_array_col_name(table_name)
    register = ""
    html_regist_textbox_template = """
        <form action="/regist_record/{}" method="post">
            <p><table>
            <tr>{}</tr>
            </table></p>
            <p><input type="submit" value="登録"><input type="reset" value="リセット"></p>
        </form>
    """
    for record in col_name:
        for field in record:
            register = register + f"""<td>{field}：<input type="text" name="{field}" size="20"></td>"""
    html_regist_textbox = html_regist_textbox_template.format(table_name, register)
    return html_regist_textbox

# 開発用。レコード登録用のbuttonを表示するhtmlを作成する。
def get_html_regist_button():
    table_name = get_array_table_name()
    register = ""
    html_regist_button_template = """
        <div>
            <table><tr><th>開発用: </th>{}</tr></table>
        </div>
    """
    for name in table_name:
        register = register + """<td><a href="/{0}"><button type="submit">{0}</button></a></td>""".format(name)    
    html_regist_button = html_regist_button_template.format(register)
    return html_regist_button

# 開発用。テーブルを表示するボタンを作成する。
def table_button_maker():
    table_array = get_array_table_name()
    html = "<table><tr>テーブルを表示する: "
    for record in table_array:
        for field in record:
            html = html + """
            <th><a href="/get_table/{0}"><button type="submit">{0}
            """.format(field) + "</button></a></th>"
    html = html + "</tr></table>"
    return html

# template.htmlに要素を埋め込む。
def contents_maker(title, contents):
    return render_template('template.html',button=table_button_maker(), title=title, contents=contents)

# レシピと作り方の入力画面を表示する。
def regist_recipe_input(menu_name):
    # 食材と調味料を選択肢から選べるようにする。
    select_food_name = html_select_maker("food", "food_name")
    select_seasoning_name = html_select_maker("seasoning", "seasoning_name")
    # レシピ登録画面
    contents = f"""
        <br>レシピの登録はこちらから。<br>
        <form action="/regist_recipe_executor/{menu_name}" method="post">
            <table>
                <tr>
                    <td>【食材】</td><td></td>
                    <td>【調味料】</td><td></td>
                </tr>
                <tr>
                    <td>食材：{select_food_name}</td>
                    <td>分量：<input type="text" name="food_quantity" size="10"></td>
                    <td>調味料：{select_seasoning_name}</td>
                    <td>分量：<input type="text" name="seasoning_quantity" size="10"></td>
                </tr>
            </table>
            <input type="submit" value="登録"><input type="reset" value="リセット">
        </form>
        <br><p>食材の登録はこちらから。</p>
        <a href="/show_food"><button type="submit">食材を登録</button></a>
    """
    return contents

# 食材を登録する
def regist_food_input():
    # 食材登録画面
    contents = f"""
        <br>食材の登録はこちらから。<br>
        <form action="/regist_food_executor" method="post">
            <table>
                <tr>
                    <td>【食材】</td><td></td><td></td>
                </tr>
                <tr>
                    <td>食材名_単位：<input type="text" name="food_name" size="10"></td>
                </tr>
                <tr><td>以下はオプション</td></tr>
    """
    col_show = ["カロリー(kcal)","炭水化物(g)","タンパク質(g)","脂質(g)","ビタミンA(μgRAE)","ビタミンB1(mg)","ビタミンB2(mg)","ビタミンB6(mg)","ビタミンB12(μg)","ビタミンC(mg)","ビタミンE(mg)","カルシウム(mg)","鉄分(mg)","食物繊維(g)", "塩分(g)"]
    col = ["calorie_kcal", "carbohydrate_g", "protein_g", "lipid_g", "vitaminA_μgRAE", "vitaminB1_mg", "vitaminB2_mg", "vitaminB6_mg", "vitaminB12_μg", "vitaminC_mg", "vitaminE_mg", "calcium_mg", "fe_mg", "dietary_fiber_g", "salt_g"]
    for num in range(15):
        contents = contents + f"""
            <tr>
                <td>{col_show[num]}：<input type="text" name="{col[num]}" size="10"></td>
            </tr>
        """
    contents = contents + """
        </table>
        <input type="submit" value="登録"><input type="reset" value="リセット"></p>
        </form>
    """
    return contents

def regist_menu_input():
    # メニュー登録画面
    contents = f"""
        <br>メニューの登録はこちらから。<br>
        <form action="/regist_menu_executor" method="post">
            <table>
                <tr>
                    <td>【メニュー】</td><td></td>
                </tr>
                <tr>
                    <td>メニュー名：<input type="text" name="menu_name" size="10"></td>
                    <td>作り方：<input type="text" name="howto" size="30"></td>
                </tr>
            </table>
            <input type="submit" value="登録"><input type="reset" value="リセット"></p>
        </form>
    """
    return contents

def regist_howto_input(menu_name):
    # howto登録画面
    contents = f"""
        <br>作り方の登録はこちらから。<br>
        <form action="/regist_howto_executor" method="post">
            <p>作り方：<input type="text" name="howto" size="10">
            <input type="hidden" name="menu_name" value="{menu_name}">
            <input type="radio" name="write_method" value="add" checked="checked">既存のものに付け加える
            <input type="radio" name="write_method" value="over">新しく書き換える
            <input type="submit" value="登録"><input type="reset" value="リセット"></p>
        </form>
    """
    return contents

# 献立を登録する
def regist_kondate_input():
    # 献立登録画面
    time_slot_select = html_select_maker("time_slot", "time_slot_name")
    menu_select = html_select_maker("menu", "menu_name")
    contents = f"""
        献立の登録はこちらから。<br>
        <form action="/regist_kondate_executor" method="post">
            <table>
                <tr>
                    <td>日付：<input type="date" name="date"></td><td>時間帯：{time_slot_select}</td><td>メニュー：{menu_select}</td>
                </tr>
    """
    contents = contents + """
        </table>
        <input type="submit" value="登録"><input type="reset" value="リセット"></p>
        </form>
    """
    return contents

# テーブル名と列名から、選択肢を作成する。
def html_select_maker(table, col):
    data = []
    query = f"""
        select {col} from kondate_db.{table};
    """
    data = sql_select_executor_array(query)
    html_select = f"""<select name="{col}"><option value="">選択してください</option>"""
    for record in data: # 全ての配列要素を選択肢に登録する。。
        for field in record:
            html_select = html_select + f"""<option value="{field}">{field}</option>"""
    html_select = html_select + """</select>"""
    return html_select







### 以下、Webページ ###


@app.route("/") # トップページ。今日から1週間分の献立を表示する。
def root():
    title = "トップページ"
    # 献立を取得するsql文。
    date = ""
    time_slot_name = ""
    menu_name = ""
    query = """
        select kondate.date, time_slot.time_slot_name, menu.menu_name from kondate_db.kondate 
        inner join kondate_db.time_slot on kondate.time_slot_id = time_slot.time_slot_id
        inner join kondate_db.menu on kondate.menu_id = menu.menu_id
        where kondate.date between curdate() and curdate()+6
        order by kondate.date,kondate.time_slot_id asc;
    """
    data = []
    html_table = "<tr>"
    data = sql_select_executor_array(query) # 配列で献立表を取得する。
    contents = "こんにちは。" + regist_kondate_input()
    for record in data: # 配列に「レシピを見る」ボタンを追加し、htmlの表にする。
        for field in record:
            html_table = html_table + f"<td>{field}</td>"
        date = record[0]
        time_slot_name = record[1]
        menu_name = record[2]
        html_table = html_table + f"""
            <form action="/delete_kondate" method="post">
            <input type="hidden" name="date" value="{date}">
            <input type="hidden" name="time_slot_name" value="{time_slot_name}">
            <input type="hidden" name="menu_name" value="{menu_name}">
            <td><a href="/show_recipe/{menu_name}">レシピを見る</a></td>
            <td><input type="submit" value="削除"></td>
            </form>
            </tr>
        """   # 「レシピを見る」ボタンを追加する。
    html_col_name = "<tr><th>日付</th><th>時間帯</th><th>メニュー</th><th>レシピ</th><th>削除</th><tr>"   # 列名を追加する。
    contents = contents + "<br><br>直近 1週間間の献立は...<br>" + "<table>" + html_col_name + html_table + "</table>"  # 画面に表示したい内容をcontentsに格納する。
    return contents_maker(title, contents)   

@app.route("/regist_kondate_executor", methods=['POST'])
def regist_kondate_executor():
    date = request.form["date"]
    time_slot_name = request.form["time_slot_name"]
    menu_name = request.form["menu_name"]
    # 献立の登録   
    if date != "" and time_slot_name != "" and menu_name != "":
        query = f"""
            insert into kondate_db.kondate(date, time_slot_id, menu_id) 
            values (
                '{date}', 
                (select time_slot_id from kondate_db.time_slot where time_slot_name = '{time_slot_name}'), 
                (select menu_id from kondate_db.menu where menu_name = '{menu_name}')
            );
        """
        sql_notselect_executor(query)
    return redirect(url_for('root', _external=True))

@app.route("/show_food")    # 登録されている食材一覧を表示する。
def show_food():
    title = "食材"
    query = """
        select food_name from kondate_db.food;
    """
    html_table = sql_select_executor(query)
    html_col_name = "<tr><th>食材名_単位</th></tr>"
    contents = regist_food_input() + "<br><table>" + html_col_name + html_table + "</table>"
    return contents_maker(title, contents)


@app.route("/regist_food_executor", methods=['POST'])
def regist_food_executor():
    food_name = request.form["food_name"]
    col = ["calorie_kcal", "carbohydrate_g", "protein_g", "lipid_g", "vitaminA_μgRAE", "vitaminB1_mg", "vitaminB2_mg", "vitaminB6_mg", "vitaminB12_μg", "vitaminC_mg", "vitaminE_mg", "calcium_mg", "fe_mg", "dietary_fiber_g", "salt_g"]
    # 食材の登録   
    if food_name is not None:
        query = """
            insert into kondate_db.food(food_name
        """
        query1 = ""
        query2 = ""
        for num in range(15):
            col_val = request.form[f"{col[num]}"]
            if col_val != "":
                query1 = query1 + f"""
                    , {col[num]}
                """
                query2 = query2 + f"""
                    , {col_val}
                """
        query = query + query1 + f") values ('{food_name}'" + query2 + ");"
        sql_notselect_executor(query)
    return redirect(url_for('show_food', _external=True))


@app.route("/show_menu")
def show_menu():
    title = "メニュー"
    query = """
        select menu_name, howto from kondate_db.menu;
    """
    data = []
    data = sql_select_executor_array(query)
    html_table = ""
    for record in data:
        html_table = html_table + "<tr>"
        col_num = 0
        for field in record:
            html_table = html_table + f"<td>{field}</td>"
            if col_num == 0:
                html_table =  html_table + f"""<td><a href="/show_recipe/{field}"><button type="submit">レシピを見る</button></a></td>"""
                col_num += 1
        html_table = html_table + "</tr>"
    html_col_name = "<tr><th>メニュー名</th><th>作り方</th><th>レシピ</th></tr>"
    contents = regist_menu_input() + "<br><table>" + html_col_name + html_table + "</table>"
    return contents_maker(title, contents)

@app.route("/regist_menu_executor", methods=['POST'])
def regist_menu_executor():
    menu_name = request.form["menu_name"]
    howto = request.form["howto"]
    # メニューの登録   
    if menu_name is not None:
        query = f"""
            insert into kondate_db.menu(menu_name, howto) 
            values ('{menu_name}', '{howto}');
        """
        sql_notselect_executor(query)
    return redirect(url_for('show_menu', _external=True))


@app.route("/show_recipe/<menu_name>")  # レシピと作り方を表示する。menu_nameを受け取り、food, seasoning, howtoを返す。
def show_recipe(menu_name):
    title = menu_name + "のレシピ"
    contents = ""
    # recipe_foodとrecipe_seasoningを取得するsql。
    query = f"""
        select food_name, quantity from kondate_db.menu
        left outer join kondate_db.recipe_food on menu.menu_id = recipe_food.menu_id
        left outer join kondate_db.food on recipe_food.food_id = food.food_id
        where menu.menu_name = '{menu_name}'
        union
        select seasoning_name, quantity from kondate_db.menu
        left outer join kondate_db.recipe_seasoning on menu.menu_id = recipe_seasoning.menu_id
        left outer join kondate_db.seasoning on recipe_seasoning.seasoning_id = seasoning.seasoning_id
        where menu.menu_name = '{menu_name}';
    """
    html_table = sql_select_executor(query) # SQLを実行し、htmlの表を取得する。
    html_col_name = "<tr><th>食材</th><th>分量</th></tr>"   # 列名を追加する。
    contents = menu_name + "のレシピは...<br>" + "<table>" + html_col_name + html_table + "</table>"  # 画面に表示したい内容をcontentsに格納する。
    
    query = f"""
        select howto from kondate_db.menu
        where menu.menu_name = '{menu_name}';
    """.format(menu_name)
    howto = sql_select_executor(query) # SQLを実行し、htmlの表を取得する。
    contents = contents + f"<br>作り方は...<br>{howto}<br>" + regist_howto_input(menu_name) # howtoを追加する。
    contents = contents + regist_recipe_input(menu_name)    # レシピの入力テキストボックスを表示する。
    return contents_maker(title, contents)

@app.route("/delete_kondate", methods=['POST'])
def delete_kondate():
    date = request.form["date"]
    time_slot_name = request.form["time_slot_name"]
    menu_name = request.form["menu_name"]
    query = f"""
        delete from kondate_db.kondate
        where kondate.date = '{date}'
		and kondate.time_slot_id =
		(select time_slot_id from kondate_db.time_slot where time_slot.time_slot_name = '{time_slot_name}')
		and kondate.menu_id = 
		(select menu_id from kondate_db.menu where menu.menu_name = '{menu_name}');
    """
    sql_notselect_executor(query)
    return redirect(url_for('root', _external=True))

@app.route("/regist_howto_executor", methods=['POST'])
def regist_howto_executor():
    menu_name = request.form["menu_name"]
    howto = request.form["howto"]
    write_method = request.form["write_method"]
    if write_method == "add":
        query1 = f"""
            select howto from kondate_db.menu where menu_name = '{menu_name}';
        """
        data = []
        howto_old = ""
        data = sql_select_executor_array(query1)
        for record in data:
            for field in record:
                howto_old = field
        howto = howto_old + howto
    query = f"""
        update kondate_db.menu set howto = '{howto}' where menu_name = '{menu_name}';
    """
    sql_notselect_executor(query)
    return redirect(url_for('show_recipe', menu_name=menu_name, _external=True))

# # レシピと作り方の登録処理を実行する。
@app.route('/regist_recipe_executor/<menu_name>', methods=['POST'])
def regist_recipe_executor(menu_name):
    food_name = request.form["food_name"]
    food_quantity = request.form["food_quantity"]
    seasoning_name = request.form["seasoning_name"]
    seasoning_quantity = request.form["seasoning_quantity"]
    # 登録の実行
    # 食材の登録   
    if food_name is not None:
        query1 = f"""
            insert into kondate_db.recipe_food(menu_id, food_id, quantity) values
            (
            (select menu_id from kondate_db.menu where menu_name = '{menu_name}'),
            (select food_id from kondate_db.food where food_name = '{food_name}'),
            {food_quantity}
            );
        """
        sql_notselect_executor(query1)
    # 調味料の登録
    if seasoning_name is not None:
        query2 = f"""
            insert into kondate_db.recipe_seasoning(menu_id, seasoning_id, quantity) values
            (
                (select menu_id from kondate_db.menu where menu_name = '{menu_name}'),
                (select seasoning_id from kondate_db.seasoning where seasoning_name = '{seasoning_name}'),
                {seasoning_quantity}
            );
        """
        sql_notselect_executor(query2)
    return redirect(url_for('show_recipe', menu_name=menu_name, _external=True))

@app.route('/get_table/<table_name>')   # 各テーブルを表示する。開発用。
def get_table(table_name):
    table_name = table_name
    title = table_name
    html_regist = get_html_regist_textbox(table_name)   # 登録用テキストボックスを取得
    html_show_table = get_html_show_table(table_name)   # テーブルを取得
    contents = html_regist + html_show_table    # 画面に表示したい内容をcontentsに格納する。
    return contents_maker(title, contents)

@app.route('/regist_record/<table_name>', methods=['POST'])   # 各テーブルを表示する。開発用。
def regist_record(table_name):
    col_name = get_array_col_name(table_name)
    col_all = ""
    value_all = ""
    for record in col_name:
        for field in record:
            col_all = col_all + "{}, ".format(field)
            value = request.form[field]
            value_all = value_all + "\"{}\", ".format(value)
    col_all = col_all[:-2]
    value_all = value_all[:-2]
    query = """
        insert into kondate_db.{} ({}) values ({});
    """.format(table_name, col_all, value_all)
    sql_notselect_executor(query)
    title = table_name
    html_regist = get_html_regist_textbox(table_name)   # 登録用テキストボックスを取得
    html_show_table = get_html_show_table(table_name)   # テーブルを取得
    contents = html_regist + html_show_table    # 画面に表示したい内容をcontentsに格納する。
    return contents_maker(title, contents)
    # return query

@app.route("/get_nutrients_input")  # 栄養素をチェック。メニュー名を入力し、outputへ渡す。
def get_nutrients_input():
    title = "栄養素チェック"
    contents = """
            <form action="/get_nutrients_output" method="get">
            <p><table><tr>
                <td>栄養を見たい料理名：　</td>
                <td><input type="text" name="menu" size="20"></td>
            </tr>
            </table></p>
            <p><input type="submit" value="登録"><input type="reset" value="リセット"></p>
    """ # 画面に表示したい内容をcontentsに格納する。
    return contents_maker(title, contents)

@app.route("/get_nutrients_output", methods=['GET'])    # メニューの栄養素を表示する。
def get_nutrients_output():
    menu = request.args.get('menu') # POSTで送られてきたメニュー名を変数に格納する。
    title = menu   # ページ名はメニュー名にする。
    query = """
        select x.menu_name, x.nutrients_name, truncate(x.nutrients_quantity+y.nutrients_quantity,2)as nutrients_quantity from
        (SELECT menu.menu_name, nutrients.nutrients_name, TRUNCATE(SUM(food_nutrients_quantity.quantity*recipe_food.quantity),2 )as 'nutrients_quantity'
        FROM kondate_db.nutrients, kondate_db.food_nutrients_quantity,kondate_db.food, kondate_db.menu, kondate_db.recipe_food 
        WHERE nutrients.nutrients_id=food_nutrients_quantity.nutrients_id AND food.food_id=food_nutrients_quantity.food_id AND food.food_id=recipe_food.food_id AND menu.menu_id=recipe_food.menu_id AND menu.menu_name='{0}'
        GROUP BY nutrients_name) as x
        inner join (SELECT menu.menu_name, nutrients.nutrients_name, TRUNCATE(SUM(seasoning_nutrients_quantity.quantity*recipe_seasoning.quantity),2 )as 'nutrients_quantity'
        FROM kondate_db.nutrients, kondate_db.seasoning_nutrients_quantity,kondate_db.seasoning, kondate_db.menu, kondate_db.recipe_seasoning 
        WHERE nutrients.nutrients_id=seasoning_nutrients_quantity.nutrients_id AND seasoning.seasoning_id=seasoning_nutrients_quantity.seasoning_id AND seasoning.seasoning_id=recipe_seasoning.seasoning_id AND menu.menu_id=recipe_seasoning.menu_id AND menu.menu_name='{0}'
        GROUP BY nutrients_name) as y
        on x.menu_name=y.menu_name and x.nutrients_name=y.nutrients_name
        group by x.nutrients_name, y.nutrients_name;
    """.format(menu)    # POSTで送られてきたメニュー名の栄養を取得するSQL。
    html_table = sql_select_executor(query) # SQLを実行し、htmlの表を取得する。
    html_col_name = "<tr><td>メニュー</td><td>栄養素</td><td>値</td><tr>"   # 列名を追加する。
    contents = "<table>" + html_col_name + html_table + "</table>"  # 画面に表示したい内容をcontentsに格納する。
    return contents_maker(title, contents)

@app.route("/tomorrow") # 明日の献立を表示する。
def tomorrow():
    title = "明日の献立"
    query = """
        select kondate.date, time_slot.time_slot_name, menu.menu_name from kondate_db.kondate 
        inner join kondate_db.time_slot on kondate.time_slot_id = time_slot.time_slot_id
        inner join kondate_db.menu on kondate.menu_id = menu.menu_id
        where kondate.date = curdate()+1
    """
    html_table = sql_select_executor(query) # SQLを実行し、htmlの表を取得する。
    html_col_name = "<tr><th>日付</th><th>時間帯</th><th>メニュー</th><tr>"   # 列名を追加する。
    contents = "こんにちは。明日の献立は...<br>" + "<table>" + html_col_name + html_table + "</table>"  # 画面に表示したい内容をcontentsに格納する。
    return contents_maker(title, contents)

# @app.route("/nutrients_check_today") # 今日の献立と栄養素の合計、不足している栄養素を表示する。
# def nutrients_check_today():
    

@app.route("/regist_food_nutrients_input")
def regist_food_nutrients_input():
    title = "食品の栄養素チェック"
    contents = """
            <form action="/regist_food_nutrients_output" method="get">
            <p><table><tr>
                <td>栄養を見たい食品名：　</td>
                <td><input type="text" name="food_name" size="20"></td>
            </tr>
            </table></p>
            <p><input type="submit" value="OK"><input type="reset" value="リセット"></p>
    """ # 画面に表示したい内容をcontentsに格納する。
    return contents_maker(title, contents)

@app.route("/regist_food_nutrients_output", methods=['GET'])
def regist_food_nutrients_output():
    food_name = request.args.get('food_name')
    title = food_name

    # 栄養素の登録用テキストボックスを表示する。
    html_regist = get_html_regist_textbox("nutrients")   # 登録用テキストボックスを取得

    query = """
    select food_name, nutrients.nutrients_name, food_nutrients_quantity.quantity from kondate_db.nutrients
    left outer join kondate_db.food_nutrients_quantity on nutrients.nutrients_id = food_nutrients_quantity.nutrients_id
    left outer join kondate_db.food on food_nutrients_quantity.food_id = food.food_id
    where food_name='{}';
    """.format(food_name)  # その食品の登録されている栄養素を表示する。
    
    table = sql_select_executor(query)
    contents =  html_regist + "<table>" + table + "</table>"
    return contents_maker(title, contents)

# @app.route("/test")
# def test():
#     query = "insert into kondate_db.menu (menu_id, menu_name, howto) values(24, 'チーズリゾット', 'youtbe');"
#     sql_notselect_executor(query)
#     return query


# @app.route("/test_input", methods=['POST'])
# def test_input():
#     query = """
#     INSERT INTO kondate_db.kondate( date, time_slot_id, menu_id) VALUES('2021-01-01',  1, 1);
#     """.format(date, time_slot_id, menu_id)

### おまじない ###
if __name__ == "__main__":
    app.run(debug=True)
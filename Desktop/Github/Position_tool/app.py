from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Order, DictionaryItem, Result, init_db
from forms import OrderForm, DictionaryForm, EditOrderForm, EditResultForm, PasswordForm
import pandas as pd
from flask import jsonify
import csv
from io import StringIO
from flask import Response
from flask import request
from collections import defaultdict
from datetime import datetime
from dateutil import parser

# all paswd serve as example in a case you would like to use in production it should be handled by different way


app = Flask(__name__)
app.config['SECRET_KEY'] = 'tajnyklic' #change for your best secret key or hash
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db.init_app(app)

# Import for product list
def import_products_from_csv(filename='products.csv'):
    try:
        df = pd.read_csv(filename)
        for product in df['product'].dropna().unique():
            exists = DictionaryItem.query.filter_by(type='product', value=product).first()
            if not exists:
                db.session.add(DictionaryItem(type='product', value=product))
        db.session.commit()
        print("✅ Products imported from CSV.")
    except Exception as e:
        print(f"⚠️ Failed to import products from CSV: {e}")


with app.app_context():
    init_db()
    import_products_from_csv()

@app.route('/', methods=['GET', 'POST'])
def index():
    new_order_form = OrderForm()
    edit_order_form = EditOrderForm()
    password_form = PasswordForm()

    new_order_form.product.choices = [(item.value, item.value) for item in DictionaryItem.query.filter_by(type='product').all()]
    new_order_form.strategy.choices = [(item.value, item.value) for item in DictionaryItem.query.filter_by(type='strategy').all()]
    new_order_form.mwh_value.choices = [(int(item.value), item.value) for item in DictionaryItem.query.filter_by(type='mwh_value').all()]
    var_item = DictionaryItem.query.filter_by(type='var').order_by(DictionaryItem.id.desc()).first()
    var_value = float(var_item.value) if var_item else None

    if new_order_form.validate_on_submit():
        new_order = Order(
            source='Manual',
            entry_timestamp=datetime.now(),
            product=new_order_form.product.data,
            mwh_value=new_order_form.mwh_value.data,
            buy_sell=new_order_form.buy_sell.data,
            volume=new_order_form.volume.data,
            entry_price=new_order_form.entry_price.data,
            strategy=new_order_form.strategy.data,
            status='Open',
            exposure=0.0,
            comment=new_order_form.comment.data
        )
        db.session.add(new_order)
        db.session.commit()
        flash('Order added successfully.', 'success')
        return redirect(url_for('index'))

    orders = Order.query.filter_by(status='Open').all()

    order_dicts = [
        {
            'id': o.id,
            'product': o.product,
            'entry_price': o.entry_price,
            'volume': o.volume,
            'mwh_value': o.mwh_value,
            'buy_sell': o.buy_sell
        } for o in orders
    ]

    return render_template(
        'index.html',
        new_order_form=new_order_form,
        edit_order_form=edit_order_form,
        password_form=password_form,
        orders=orders,
        order_dicts=order_dicts,
        var_value=var_value
    )

@app.route('/api/current_prices')
def api_current_prices():
    try:
        df = pd.read_csv('current_prices.csv')
        price_dict = dict(zip(df['product'], df['price']))
        return jsonify(price_dict)  # ← Tohle je klíčové
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if file:
        df = pd.read_csv(file)
        imported = 0
        for _, row in df.iterrows():
            try:
                order = Order(
                    source='Import',
                    entry_timestamp=parser.parse(row['entry_timestamp']).replace(second=0),
                    product=row['product'],
                    mwh_value=int(row.get('mwh_value', 24)),
                    buy_sell=row.get('buy_sell', 'Buy'),
                    volume=float(row['volume']),
                    entry_price=float(row['entry_price']),
                    strategy=row['strategy'],
                    status=row.get('status', 'Open'),
                    exposure=0.0,
                    comment=row.get('comment', '')
                )
                db.session.add(order)
                imported += 1
            except Exception as e:
                print(f"⚠️ Skipped row due to error: {e}")
        db.session.commit()
        flash(f'{imported} orders imported successfully.', 'success')
    else:
        flash('No file selected.', 'danger')
    return redirect(url_for('index'))


@app.route('/edit_order/<int:order_id>', methods=['POST'])
def edit_order(order_id):
    order = Order.query.get_or_404(order_id)
    form = EditOrderForm()

    # needed for form validation
    form.product.choices = [(item.value, item.value) for item in DictionaryItem.query.filter_by(type='product').all()]
    form.strategy.choices = [(item.value, item.value) for item in DictionaryItem.query.filter_by(type='strategy').all()]

    if form.validate_on_submit():
        order.comment = form.comment.data
        if form.exit_price.data:
            # If exit price filled go save
            order.exit_price = form.exit_price.data
            order.status = 'Closed'
            order.exit_timestamp = datetime.now().replace(second=0)
            result = Result(
                source=order.source,
                entry_timestamp=order.entry_timestamp,
                product=order.product,
                mwh_value=order.mwh_value,
                buy_sell=order.buy_sell,
                volume=order.volume,
                entry_price=order.entry_price,
                strategy=order.strategy,
                exit_price=order.exit_price,
                exit_timestamp=order.exit_timestamp,
                exposure=order.exposure,
                comment=order.comment
            )
            db.session.add(result)
            db.session.delete(order)
            db.session.commit()
            flash('Order closed and moved to Results.', 'success')
        else:
            # When you have no exit price, just save comment
            db.session.commit()
            flash('Comment updated successfully.', 'success')

    return redirect(url_for('index'))

@app.route('/delete_order/<int:order_id>', methods=['POST'])
def delete_order(order_id):
    form = PasswordForm()
    if form.validate_on_submit():
        if form.password.data == 'admin123':
            order = Order.query.get_or_404(order_id)
            db.session.delete(order)
            db.session.commit()
            flash('Order deleted.', 'success')
        else:
            flash('Incorrect password.', 'error')
    return redirect(url_for('index'))

@app.route('/results')
def results():
    results = Result.query.order_by(Result.id.desc()).all()
    edit_result_form = EditResultForm()
    password_form = PasswordForm()

    edit_result_form.product.choices = [(item.value, item.value) for item in DictionaryItem.query.filter_by(type='product').all()]
    edit_result_form.strategy.choices = [(item.value, item.value) for item in DictionaryItem.query.filter_by(type='strategy').all()]
    edit_result_form.mwh_value.choices = [(item.value, item.value) for item in DictionaryItem.query.filter_by(type='mwh_value').all()
    ]
    return render_template(
        'results.html',
        results=results,
        edit_result_form=edit_result_form,
        password_form=password_form
    )

@app.route('/edit_result/<int:result_id>', methods=['POST'])
def edit_result(result_id):
    result = Result.query.get_or_404(result_id)
    form = EditResultForm()
    password = request.form.get('password')

    form.product.choices = [(item.value, item.value) for item in DictionaryItem.query.filter_by(type='product').all()]
    form.strategy.choices = [(item.value, item.value) for item in DictionaryItem.query.filter_by(type='strategy').all()]
    form.mwh_value.choices = [(item.value, item.value) for item in DictionaryItem.query.filter_by(type='mwh_value').all()]

    if password != 'admin123':
        flash('Incorrect password.', 'error')
        return redirect(url_for('results'))

    if form.validate_on_submit():
        result.product = form.product.data
        result.mwh_value = form.mwh_value.data
        result.buy_sell = form.buy_sell.data
        result.volume = form.volume.data
        result.entry_price = form.entry_price.data
        result.exit_price = form.exit_price.data
        result.strategy = form.strategy.data
        result.comment = form.comment.data
        db.session.commit()
        flash('Result updated successfully.', 'success')

    return redirect(url_for('results'))

@app.route('/delete_result/<int:result_id>', methods=['POST'])
def delete_result(result_id):
    form = PasswordForm()
    if form.validate_on_submit() and form.password.data == 'admin123':
        result = Result.query.get_or_404(result_id)
        db.session.delete(result)
        db.session.commit()
        flash('Result deleted.', 'success')
    else:
        flash('Incorrect password.', 'danger')
    return redirect(url_for('results'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    form = DictionaryForm()
    password_form = PasswordForm()  # ← přidáno

    existing_types = db.session.query(DictionaryItem.type).distinct().all()
    form.type.choices = [(etype[0], etype[0]) for etype in existing_types]

    if form.validate_on_submit():
        exists = DictionaryItem.query.filter_by(type=form.type.data, value=form.value.data).first()
        if exists:
            flash('This combination already exists.', 'error')
        else:
            db.session.add(DictionaryItem(type=form.type.data, value=form.value.data))
            db.session.commit()
            flash('Dictionary item added.', 'success')
        return redirect(url_for('admin'))

    dictionaries_by_type = {}
    all_items = DictionaryItem.query.all()
    for item in all_items:
        dictionaries_by_type.setdefault(item.type, []).append(item)

    return render_template('admin.html', form=form, password_form=password_form, dictionaries_by_type=dictionaries_by_type)



@app.route('/upload_products', methods=['POST'])
def upload_products():
    file = request.files['file']
    if file and file.filename.endswith('.csv'):
        df = pd.read_csv(file)
        added = 0
        for value in df['product'].dropna().unique():
            if not DictionaryItem.query.filter_by(type='product', value=value).first():
                db.session.add(DictionaryItem(type='product', value=value))
                added += 1
        db.session.commit()
        flash(f'{added} new product(s) imported.', 'success')
    else:
        flash('Please upload a valid CSV file with a "product" column.', 'danger')
    return redirect(url_for('admin'))


@app.route('/delete_item/<int:item_id>')
def delete_item(item_id):
    item = DictionaryItem.query.get(item_id)
    if item:
        db.session.delete(item)
        db.session.commit()
        flash('Dictionary item deleted.', 'success')
    return redirect(url_for('admin'))


@app.route('/reset_database', methods=['POST'])
def reset_database():
    form = PasswordForm()
    if form.validate_on_submit() and form.password.data == 'admin123':
        db.session.query(Order).delete()
        db.session.query(Result).delete()
        db.session.query(DictionaryItem).delete()
        db.session.commit()
        flash('Orders and Results cleared. Dictionary reset to defaults. Please restart the application to apply changes.', 'warning')
    else:
        flash('Incorrect password.', 'danger')
    return redirect(url_for('admin'))


@app.route('/statistics')
def statistics():
    # Parameters for filtr currently used just strategy
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    selected_strategy = request.args.get('strategy')

    # read all strategies for <select>
    all_strategies_query = db.session.query(Result.strategy).distinct().all()
    all_strategies = sorted([s[0] for s in all_strategies_query])

    query = Result.query

    if selected_strategy:
        query = query.filter_by(strategy=selected_strategy)

    if start_date:
        query = query.filter(Result.entry_timestamp >= datetime.strptime(start_date, "%Y-%m-%d %H:%M"))
    if end_date:
        query = query.filter(Result.entry_timestamp <= datetime.strptime(start_date, "%Y-%m-%d %H:%M"))

    results = query.order_by(Result.id).all()

    # Calculation for statistics
    total_trades = len(results)
    trades_with_pnl = []
    cumulative_pnl = []
    running_total = 0
    win_count = 0
    total_profit, total_loss = 0, 0

    for r in results:
        diff = r.exit_price - r.entry_price if r.buy_sell == 'Buy' else r.entry_price - r.exit_price
        pnl = diff * r.volume * r.mwh_value
        if pnl > 0:
            win_count += 1
            total_profit += pnl
        else:
            total_loss += pnl
        running_total += pnl
        cumulative_pnl.append({'id': r.id, 'pnl': round(running_total, 2)})
        trades_with_pnl.append({**r.__dict__, 'pnl': pnl})

    win_rate = round((win_count / total_trades) * 100, 2) if total_trades else 0
    profit_factor = round(total_profit / abs(total_loss), 2) if total_loss != 0 else '∞'
    total_pnl = round(total_profit + total_loss, 2)

    # Drawdown
    max_dd = 0
    peak = cumulative_pnl[0]['pnl'] if cumulative_pnl else 0
    max_dd_duration = 0
    current_duration = 0

    for point in cumulative_pnl:
        if point['pnl'] > peak:
            peak = point['pnl']
            current_duration = 0
        else:
            dd = peak - point['pnl']
            current_duration += 1
            if dd > max_dd:
                max_dd = dd
                max_dd_duration = current_duration

    # Profitability per strategy
    strategy_stats = defaultdict(list)
    for t in trades_with_pnl:
        strategy_stats[t['strategy']].append(t['pnl'])

    strategy_table = []
    for strat, pnl_list in strategy_stats.items():
        count = len(pnl_list)
        avg_pnl = round(sum(pnl_list) / count, 2)
        wins = len([p for p in pnl_list if p > 0])
        winr = round((wins / count) * 100, 2) if count else 0
        strategy_table.append({
            'strategy': strat,
            'count': count,
            'avg': avg_pnl,
            'winrate': winr
        })

    # Top 5 trades
    top_trades = sorted(trades_with_pnl, key=lambda x: x['pnl'], reverse=True)[:5]

    return render_template(
        'statistics.html',
        total_trades=total_trades,
        win_rate=win_rate,
        profit_factor=profit_factor,
        total_pnl=total_pnl,
        strategy_table=strategy_table,
        top_trades=top_trades,
        cumulative_pnl=cumulative_pnl,
        max_dd=round(max_dd, 2),
        max_dd_duration=max_dd_duration,
        all_strategies=all_strategies
    )


@app.route('/export_results_csv')
def export_results_csv():
    results = Result.query.order_by(Result.id).all()

    si = StringIO()
    cw = csv.writer(si)

    # CSV export header
    cw.writerow([
        'ID', 'Product', 'Strategy', 'Buy/Sell', 'Volume',
        'MWh/Unit', 'Entry Price', 'Exit Price',
        'Entry Timestamp', 'Exit Timestamp', 'Exposure', 'Comment'
    ])

    for r in results:
        cw.writerow([
            r.id, r.product, r.strategy, r.buy_sell, r.volume,
            r.mwh_value, r.entry_price, r.exit_price,
            r.entry_timestamp, r.exit_timestamp, r.exposure, r.comment
        ])

    output = si.getvalue()
    return Response(output,
                    mimetype="text/csv",
                    headers={"Content-Disposition": "attachment;filename=closed_deals.csv"})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

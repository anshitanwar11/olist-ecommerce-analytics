"""Leakage-aware feature engineering for Olist satisfaction predictions."""
from __future__ import annotations
import numpy as np
import pandas as pd

NUMERIC_FEATURES = [
    "purchase_year", "purchase_month_num", "purchase_weekday", "purchase_hour",
    "n_items", "n_sellers", "price_sum", "freight_sum", "freight_ratio",
    "max_installments", "credit_card_amt", "debit_card_amt", "boleto_amt",
    "voucher_amt", "not_defined_amt", "payment_rows", "avg_weight_g",
    "avg_volume_cm3", "avg_photos_qty", "distinct_categories", "same_state",
]
CATEGORICAL_FEATURES = ["customer_state", "dominant_category", "seller_state"]
FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def _col(df, names):
    lower={str(c).strip().lower():c for c in df.columns}
    for n in names:
        if n.lower() in lower: return lower[n.lower()]
    return None


def _num(df, names, default=np.nan):
    c=_col(df,names)
    if c is None: return pd.Series(default,index=df.index,dtype='float64')
    return pd.to_numeric(df[c],errors='coerce')


def _mode_or_nan(s):
    s=s.dropna()
    if s.empty: return np.nan
    m=s.mode()
    return m.iloc[0] if not m.empty else np.nan


def build_model_frame(order_360: pd.DataFrame, items: pd.DataFrame, products: pd.DataFrame, seller_lookup: pd.DataFrame | None = None) -> pd.DataFrame:
    """Return one row per reviewed order with only plausible order-time predictors plus review_score target.

    Delivery outcomes, final status, review metadata/text, and identifiers are excluded from predictors.
    """
    if order_360 is None or order_360.empty: raise ValueError('order_360 is empty.')
    if items is None or items.empty: raise ValueError('items is empty.')
    o=order_360.copy()
    order_id=_col(o,['order_id']); score_col=_col(o,['review_score','average_review_score','avg_review_score'])
    purchase_col=_col(o,['purchase_dt','order_purchase_timestamp','purchase_timestamp'])
    if order_id is None or score_col is None: raise KeyError('order_360 requires order_id and review_score.')
    o=o.rename(columns={order_id:'order_id',score_col:'review_score'})
    if purchase_col: o=o.rename(columns={purchase_col:'_purchase_dt'})
    else: o['_purchase_dt']=pd.NaT
    o['_purchase_dt']=pd.to_datetime(o['_purchase_dt'],errors='coerce',utc=True).dt.tz_convert(None)
    o['review_score']=pd.to_numeric(o['review_score'],errors='coerce')
    # Keep orders with missing reviews here: they may still train supporting
    # delivery-outcome models. The review model filters to valid scores in train_model.py.
    o=o.drop_duplicates('order_id',keep='first')
    base=pd.DataFrame({'order_id':o['order_id'],'review_score':o['review_score']})
    dt=o['_purchase_dt']
    base['purchase_year']=dt.dt.year
    base['purchase_month_num']=dt.dt.month
    base['purchase_weekday']=dt.dt.dayofweek
    base['purchase_hour']=dt.dt.hour
    state_col=_col(o,['customer_state','state_customer'])
    base['customer_state']=o[state_col].astype('string') if state_col else 'Unknown'
    # Payment and checkout values from order_360 are known at/near purchase time.
    for c, aliases in {
        'max_installments':['max_installments','payment_installments','installments'],
        'credit_card_amt':['credit_card_amt'], 'debit_card_amt':['debit_card_amt'],
        'boleto_amt':['boleto_amt'], 'voucher_amt':['voucher_amt'],
        'not_defined_amt':['not_defined_amt'], 'payment_rows':['payment_rows'],
    }.items(): base[c]=_num(o,aliases).to_numpy()
    item=o.copy()
    item_source=items.copy()
    oid=_col(item_source,['order_id']); price_col=_col(item_source,['price','item_price']); freight_col=_col(item_source,['freight_value','freight'])
    if oid is None: raise KeyError('items requires order_id.')
    item_source=item_source.rename(columns={oid:'order_id'})
    item_source['_price']=pd.to_numeric(item_source[price_col],errors='coerce') if price_col else np.nan
    item_source['_freight']=pd.to_numeric(item_source[freight_col],errors='coerce') if freight_col else np.nan
    item_agg=item_source.groupby('order_id').agg(
        n_items=('order_id','size'), n_sellers=('seller_id','nunique') if 'seller_id' in item_source.columns else ('order_id','size'),
        price_sum=('_price',lambda x:x.sum(min_count=1)),freight_sum=('_freight',lambda x:x.sum(min_count=1)),
    ).reset_index()
    base=base.merge(item_agg,on='order_id',how='left')
    # Make item feature build safe with the actual schema: category_en, weight_g, volume_cm3, photos_qty.
    product_id_items=_col(item_source,['product_id']); product_id_products=_col(products,['product_id'])
    if product_id_items and product_id_products:
        p=products.copy().rename(columns={product_id_products:'product_id'})
        aliases={}
        for canonical, candidates in {
            'category_en':['category_en','product_category_name_english','product_category_name','category_name'],
            'weight_g':['weight_g','product_weight_g','product_weight'],
            'volume_cm3':['volume_cm3','product_volume_cm3'],
            'photos_qty':['photos_qty','product_photos_qty','photos'],
        }.items():
            found=_col(p,candidates)
            if found: aliases[found]=canonical
        p=p.rename(columns=aliases)
        cols=['product_id']+[c for c in ['category_en','weight_g','volume_cm3','photos_qty'] if c in p.columns]
        joined=item_source.rename(columns={product_id_items:'product_id'}).merge(p[cols].drop_duplicates('product_id'),on='product_id',how='left')
    else:
        joined=item_source.copy(); joined['category_en']=np.nan
    for c in ['weight_g','volume_cm3','photos_qty']:
        if c not in joined.columns: joined[c]=np.nan
        joined[c]=pd.to_numeric(joined[c],errors='coerce')
    if 'category_en' not in joined.columns: joined['category_en']=np.nan
    item_features=joined.groupby('order_id').agg(
        avg_weight_g=('weight_g','mean'),avg_volume_cm3=('volume_cm3','mean'),avg_photos_qty=('photos_qty','mean'),
        distinct_categories=('category_en','nunique'),
    ).reset_index()
    dom=(joined.dropna(subset=['category_en']).groupby(['order_id','category_en']).size().rename('n').reset_index().sort_values(['order_id','n','category_en'],ascending=[True,False,True]).drop_duplicates('order_id'))
    item_features=item_features.merge(dom[['order_id','category_en']].rename(columns={'category_en':'dominant_category'}),on='order_id',how='left')
    base=base.merge(item_features,on='order_id',how='left')
    # Seller geography is permitted as an order-time proxy; never use seller performance metrics.
    base['seller_state']='Unknown'
    if seller_lookup is not None and not seller_lookup.empty and 'seller_id' in item_source.columns:
        sl=seller_lookup.copy(); sid=_col(sl,['seller_id']); sstate=_col(sl,['state','seller_state'])
        if sid and sstate:
            sl=sl.rename(columns={sid:'seller_id',sstate:'seller_state'})[['seller_id','seller_state']].drop_duplicates('seller_id')
            sellers=item_source[['order_id','seller_id']].merge(sl,on='seller_id',how='left')
            seller_states=sellers.groupby('order_id')['seller_state'].agg(_mode_or_nan).reset_index()
            base=base.drop(columns=['seller_state']).merge(seller_states,on='order_id',how='left')
    base['same_state']=((base['customer_state'].astype('string').str.upper()==base['seller_state'].astype('string').str.upper()) & base['customer_state'].notna() & base['seller_state'].notna()).astype(float)
    base['freight_ratio']=base['freight_sum']/base['price_sum'].replace({0:np.nan})
    # Ensure stable complete schema for inference.
    for c in FEATURE_COLUMNS:
        if c not in base.columns: base[c]=np.nan
    return base[['order_id','review_score']+FEATURE_COLUMNS].reset_index(drop=True)


def get_prediction_feature_columns(frame: pd.DataFrame | None = None) -> list[str]:
    return list(FEATURE_COLUMNS)


def prediction_row(values: dict) -> pd.DataFrame:
    row={c:values.get(c,np.nan) for c in FEATURE_COLUMNS}
    row['freight_ratio']=row.get('freight_sum',np.nan)/row.get('price_sum',np.nan) if pd.notna(row.get('price_sum')) and row.get('price_sum') not in [0,None] else np.nan
    cust=str(row.get('customer_state','Unknown')).upper(); sell=str(row.get('seller_state','Unknown')).upper()
    row['same_state']=int(cust==sell and cust not in ('UNKNOWN','NAN',''))
    return pd.DataFrame([row],columns=FEATURE_COLUMNS)

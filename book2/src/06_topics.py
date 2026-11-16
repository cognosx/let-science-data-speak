# %% [markdown]
# # 06 — Topics and trends (Book 2, Chapter 6)
# Embeddings (all-MiniLM-L6-v2) + BERTopic. Trends are shares of each year's output, not counts.

# %%
import numpy as np, pandas as pd, re
from pathlib import Path
ROOT = Path("..").resolve() if Path("../config.yml").exists() else Path(".").resolve()
RAW, FIN, LOGS, INT = ROOT/"data/raw", ROOT/"data/final", ROOT/"logs", ROOT/"data/interim"
pm = pd.read_json(sorted(RAW.glob("pubmed_*.jsonl"))[-1], lines=True, dtype={"pmid": str})
pm = pm[pm["abstract"].notna() & pm["year"].notna()].reset_index(drop=True)
docs = (pm["title"].fillna("") + ". " + pm["abstract"]).tolist()
print(len(docs), "records with an abstract")

# %%
from sentence_transformers import SentenceTransformer
emb_file = INT/"embeddings_minilm.npy"
if emb_file.exists(): emb = np.load(emb_file)
else:
    emb = SentenceTransformer("all-MiniLM-L6-v2").encode(docs, batch_size=64, show_progress_bar=False, normalize_embeddings=True)
    np.save(emb_file, emb)
emb.shape

# %%
from bertopic import BERTopic
from umap import UMAP; from hdbscan import HDBSCAN
from sklearn.feature_extraction.text import CountVectorizer
stop = list(CountVectorizer(stop_words="english").get_stop_words()) + ["malaria","vaccine","vaccines","plasmodium","study","studies","results","using","used"]
tm = BERTopic(umap_model=UMAP(n_neighbors=15, n_components=5, min_dist=0.0, metric="cosine", random_state=2026),
              hdbscan_model=HDBSCAN(min_cluster_size=60, metric="euclidean", prediction_data=True),
              vectorizer_model=CountVectorizer(stop_words=stop, ngram_range=(1,2), min_df=5))
topics, _ = tm.fit_transform(docs, emb)
info = tm.get_topic_info()
print("topics:", (info.Topic >= 0).sum(), "| outliers:", round((np.array(topics) == -1).mean(), 3))
info[["Topic","Count","Name"]].head(30)

# %% [markdown]
# Outliers are reassigned to their nearest topic so that trends use every record; the share
# left as outlier is reported above.

# %%
topics2 = tm.reduce_outliers(docs, topics, strategy="embeddings", embeddings=emb)
pm["topic"] = topics2
names = {r.Topic: r.Name for r in info.itertuples()}
pm["topic_name"] = pm["topic"].map(names)
pm["period"] = pd.cut(pm["year"], [0,1999,2009,2019,2026], labels=["≤1999","2000–09","2010–19","2020–26"])
share = pd.crosstab(pm["topic_name"], pm["period"], normalize="columns").round(3)
share["change"] = share["2020–26"] - share["2010–19"]
print(share.sort_values("change").head(6).to_string()); print(share.sort_values("change").tail(6).to_string())
pm[["pmid","year","topic","topic_name"]].to_parquet(FIN/"topics.parquet", index=False)
info.to_csv(LOGS/"topic_info.csv", index=False)

# %% [markdown]
# ## Stability check: refit with a different seed and compare
# %%
tm2 = BERTopic(umap_model=UMAP(n_neighbors=15, n_components=5, min_dist=0.0, metric="cosine", random_state=7),
               hdbscan_model=HDBSCAN(min_cluster_size=60, prediction_data=True),
               vectorizer_model=CountVectorizer(stop_words=stop, ngram_range=(1,2), min_df=5))
t2, _ = tm2.fit_transform(docs, emb)
from sklearn.metrics import adjusted_rand_score
m = (np.array(topics) >= 0) & (np.array(t2) >= 0)
print("topics in refit:", len(set(t2)) - (1 if -1 in t2 else 0),
      "| adjusted Rand index (non-outliers in both):", round(adjusted_rand_score(np.array(topics)[m], np.array(t2)[m]), 2))

# %% [markdown]
# ## A second lens: OpenAlex topics
# OpenAlex assigns each work a primary topic, subfield and field with its own classifier.
# Comparing it with our clusters shows where the two lenses agree, and what the odd clusters hold.

# %%
oe_file = FIN / "openalex_enrich.parquet"
if oe_file.exists():
    oe = pd.read_parquet(oe_file)[["pmid", "primary_topic", "primary_field"]]
    t = pm[["pmid", "topic", "topic_name", "year"]].merge(oe, on="pmid", how="left")
    print("records with an OpenAlex topic:", t.primary_topic.notna().mean().round(3))
    print("Top OpenAlex primary topics:\n", t.primary_topic.value_counts().head(10).to_string())
    print("\nOpenAlex fields:\n", t.primary_field.value_counts(normalize=True).head(6).round(3).to_string())
    for kw in ["travel", "leishman"]:
        lab = [n for n in t.topic_name.dropna().unique() if kw in n][0]
        sub = t[t.topic_name == lab]
        print(f"\nCluster '{lab}' ({len(sub)} papers): top OpenAlex topics\n", sub.primary_topic.value_counts().head(4).to_string())
    # Agreement: how concentrated is each BERTopic cluster in one OpenAlex topic?
    conc = t.dropna(subset=["primary_topic"]).groupby("topic_name").primary_topic.agg(lambda s: s.value_counts(normalize=True).iloc[0])
    print("\nMedian share of a cluster's papers in its most common OpenAlex topic:", round(conc.median(), 2))

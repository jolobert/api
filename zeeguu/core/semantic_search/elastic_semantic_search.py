from elasticsearch import Elasticsearch
from elastic_transport import ConnectionError

from zeeguu.core.model import (
    Article,
)

from zeeguu.core.elastic.elastic_query_builder import (
    build_elastic_semantic_sim_query,
    build_elastic_semantic_sim_query_for_topic_cls,
    build_elastic_semantic_sim_query_for_text,
    more_like_this_query,
)
from zeeguu.core.util.timer_logging_decorator import time_this
from zeeguu.core.elastic.settings import ES_CONN_STRING, ES_ZINDEX
from zeeguu.core.semantic_vector_api import (
    get_embedding_from_article,
    get_embedding_from_text,
)


@time_this
def article_semantic_search_for_user(
    user,
    count,
    search_terms,
):
    return NotImplementedError


@time_this
def articles_like_this_tfidf(article: Article):
    query_body = more_like_this_query(10, article.content, article.language)
    es = Elasticsearch(ES_CONN_STRING)
    res = es.search(index=ES_ZINDEX, body=query_body)
    final_article_mix = []
    hit_list = res["hits"].get("hits")
    final_article_mix.extend(_to_articles_from_ES_hits(hit_list))

    return [a for a in final_article_mix if a is not None and not a.broken], hit_list


@time_this
def articles_like_this_semantic(article: Article):
    query_body = build_elastic_semantic_sim_query(
        10, article.language, get_embedding_from_article(article), article
    )
    final_article_mix = []

    try:
        es = Elasticsearch(ES_CONN_STRING)
        res = es.search(index=ES_ZINDEX, body=query_body)

        hit_list = res["hits"].get("hits")
        final_article_mix.extend(_to_articles_from_ES_hits(hit_list))

        return [
            a for a in final_article_mix if a is not None and not a.broken
        ], hit_list
    except ConnectionError:
        print("Could not connect to ES server.")
    except Exception as e:
        print(f"Error encountered: {e}")
    return [], []


@time_this
def add_topics_based_on_semantic_hood_search(
    article: Article, k: int = 9
):  # hood = (slang) neighborhood
    query_body = build_elastic_semantic_sim_query_for_topic_cls(
        k, article, get_embedding_from_article(article)
    )
    final_article_mix = []

    try:
        es = Elasticsearch(ES_CONN_STRING)
        res = es.search(index=ES_ZINDEX, body=query_body)

        hit_list = res["hits"].get("hits")
        final_article_mix.extend(_to_articles_from_ES_hits(hit_list))

        return [
            a for a in final_article_mix if a is not None and not a.broken
        ], hit_list
    except ConnectionError:
        print("Could not connect to ES server.")
    except Exception as e:
        print(f"Error encountered: {e}")
    return [], []


@time_this
def find_articles_based_on_text(text, k: int = 9):  # hood = (slang) neighborhood
    query_body = build_elastic_semantic_sim_query_for_text(
        k, get_embedding_from_text(text)
    )
    final_article_mix = []

    try:
        es = Elasticsearch(ES_CONN_STRING)
        res = es.search(index=ES_ZINDEX, body=query_body)

        hit_list = res["hits"].get("hits")
        final_article_mix.extend(_to_articles_from_ES_hits(hit_list))

        return [
            a for a in final_article_mix if a is not None and not a.broken
        ], hit_list
    except ConnectionError:
        print("Could not connect to ES server.")
    except Exception as e:
        print(f"Error encountered: {e}")
    return [], []


def _to_articles_from_ES_hits(hits):
    articles = []
    for hit in hits:
        articles.append(Article.find_by_id(hit.get("_id")))
    return articles

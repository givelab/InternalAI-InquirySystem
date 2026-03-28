# xxxxxxxxxxx


### dbセットアップ

```


make generate-migrations message="add tasks table"
```


------------------

### 残っている古いコンテナやネットワーク衝突の改善

```
docker system prune -af --volumes


```

### DBマイグレーション参照バグが起きないか確認

```
# 念のため完全再ビルド
docker compose build --no-cache

# DB を先に立ち上げる
docker compose up -d db



# ホスト側でマイグレーション生成 & 適用
make generate-migrations message="init"
# ここで "Can't locate revision identified by 'fdbcf325ec40'" がもう出ないか確認
# 生成された migrations/versions/xxxx_init.py を確認
make migrate


# 最後に docker compose up -d
backend コンテナが make migrate するかもしれませんが、既に最新状態なら何もしないで正常起動するはず

```

# 共同小屋素材（v1-B）

本目录提供共同小屋全屋场景底图、家具单品图和未拥有家具的遮罩素材。场景底图与遮罩使用同一画布坐标系，前端按原尺寸比例叠加显示。

```text
cottage/
├─ base.png       全屋家具母图，1536 × 1024
├─ items/         13 张家具单品 PNG，用于家具展示
└─ locked/        每件家具各有 PNG 遮罩和 SVG 后备遮罩，共 13 组
```

## 命名

家具遮罩文件名使用家具配置中的 `asset_key`：

- `items/<asset_key>.png`
- `locked/<asset_key>.png`
- `locked/<asset_key>.svg`

当前 `items/` 和 `locked/` 均包含全部 13 件家具对应素材。代码中的商品 id 与 `asset_key` 不同的项目，以配置中的 `asset_key` 作为文件名。

## 场景显示

- 前端以 `base.png` 作为全屋底图。
- 未拥有的家具叠加 `locked/<asset_key>.png`，显示其锁定状态。
- 已拥有的家具不叠加锁定遮罩，由底图显示家具。
- PNG 遮罩加载失败时，前端改用同名 SVG 遮罩。

`base.png` 与所有锁定遮罩的画布为 1536 × 1024，位置已对齐，可随场景等比例缩放。

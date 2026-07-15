# 日課管理アプリ

Python、Tkinter、SQLite、Matplotlibで作成したデスクトップアプリです。

## 実装済み機能
- 日課項目の追加
- 日課項目の一覧表示
- 日課項目の編集
- 日課項目の削除
- 日々の数値記録
- 過去の記録表示
- 目標設定
- 同じ日課への目標再設定（上書き）
- 目標達成判定
- 期間指定グラフ
- グラフ表示時の最新データ自動読込
## 実装していない機能
- 記録の編集
- 目標の削除
- 他ユーザとの共有
## セットアップ
### 1. Pythonを確認
```bash
python --version
```
Windowsで上記が動かない場合：
```bash
py --version
```
### 2. 仮想環境を作成
```bash
python -m venv .venv
```
Windows PowerShell：
```powershell
.venv\Scripts\Activate.ps1
```
Windows コマンドプロンプト：
```cmd
.venv\Scripts\activate
```
### 3. ライブラリをインストール
```bash
pip install -r requirements.txt
```
### 4. 実行
```bash
python app.py
```
## 補足
- データは同じフォルダ内の `habit_tracker.db` に保存されます。
- `habit_tracker.db` を削除すると、すべての登録内容が初期化されます。

flowchart LR

User([利用者])

subgraph 日課管理アプリ

UC1([日課項目を追加する])
UC2([日課項目を表示する])
UC3([日課項目を編集する])
UC4([日課項目を削除する])

UC5([日課データを記録する])
UC6([日課データを閲覧する])

UC7([目標を設定する<br/>（再設定を含む）])
UC8([達成状況を表示する])

UC9([期間を設定する])
UC10([グラフを表示する])

UC11([入力内容を検証する])
UC12([達成判定を行う])

UC13([確認メッセージを表示する])
UC14([エラーメッセージを表示する])

end

User --> UC1
User --> UC2
User --> UC3
User --> UC4

User --> UC5
User --> UC6

User --> UC7
User --> UC8

User --> UC10

UC1 -.include.-> UC11
UC3 -.include.-> UC11
UC5 -.include.-> UC11
UC7 -.include.-> UC11

UC5 -.include.-> UC12
UC8 -.include.-> UC12

UC10 -.include.-> UC9

UC4 -.include.-> UC13

UC14 -.extend.-> UC1
UC14 -.extend.-> UC3
UC14 -.extend.-> UC5
UC14 -.extend.-> UC7
UC14 -.extend.-> UC10

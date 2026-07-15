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
```mermaid
flowchart LR

User([利用者])

subgraph App["日課管理アプリ"]

UC1([日課項目を追加する])
UC2([日課項目を表示する])
UC3([日課項目を編集する])
UC4([日課項目を削除する])

UC5([日課データを記録する])
UC6([日課データを閲覧する])

UC7([目標設定（再設定を含む）])
UC8([達成状況を表示する])

UC9([表示期間を設定する])
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

UC1 -. include .-> UC11
UC3 -. include .-> UC11
UC5 -. include .-> UC11
UC7 -. include .-> UC11

UC5 -. include .-> UC12
UC8 -. include .-> UC12

UC10 -. include .-> UC9

UC4 -. include .-> UC13

UC14 -. extend .-> UC1
UC14 -. extend .-> UC3
UC14 -. extend .-> UC5
UC14 -. extend .-> UC7
UC14 -. extend .-> UC10

GoalService --> Goal

RecordService --> DailyRecord

HabitService --> Habit

GraphService --> DisplayPeriod
```
```mermaid
classDiagram

class Habit {
    +int habitId
    +String name
    +String unit
    +Date createdDate
    +bool isActive
    +rename(name : String)
    +changeUnit(unit : String)
    +delete()
}

class DailyRecord {
    +int recordId
    +Date recordDate
    +float value
}

class Goal {
    +int goalId
    +float targetValue
    +String comparisonType
    +isAchieved(value : float) bool
}

class DisplayPeriod {
    +Date startDate
    +Date endDate
    +validate() bool
}

class HabitService {
    +createHabit()
    +getHabit()
    +updateHabit()
    +deleteHabit()
}

class RecordService {
    +saveRecord()
    +getRecords()
}

class GoalService {
    +setGoal()
    +judgeAchievement()
}

class GraphService {
    +createGraph()
    +getGraphData()
}

HabitService --> Habit
RecordService --> DailyRecord
GoalService --> Goal
GraphService --> DailyRecord
GraphService --> DisplayPeriod

Habit "1" --> "0..*" DailyRecord : records
Habit "1" --> "0..1" Goal : goal
```
```mermaid
sequenceDiagram
    actor User as 利用者
    participant UI as 操作画面
    participant RecordService as 記録サービス
    participant GoalService as 目標サービス
    participant GraphService as グラフサービス

    User->>UI: 日課項目と数値を入力
    User->>UI: 保存ボタンを押す
    UI->>UI: 入力内容を検証する

    alt 入力内容が不正
        UI-->>User: エラーメッセージを表示
    else 入力内容が正常
        UI->>RecordService: saveRecord(habitId, date, value)
        RecordService-->>UI: 保存結果

        alt 保存に失敗
            UI-->>User: 保存失敗メッセージを表示
        else 保存に成功
            UI->>GoalService: judgeAchievement(habitId, value)
            GoalService-->>UI: 達成結果
            UI-->>User: 保存完了と達成状況を表示
        end
    end

    User->>UI: グラフ表示を選択
    UI->>UI: 表示期間を検証する

    alt 期間が不正
        UI-->>User: 期間入力エラーを表示
    else 期間が正常
        UI->>GraphService: createGraph(habitId, startDate, endDate)
        GraphService-->>UI: 最新のGraphData
        UI-->>User: 最新データのグラフを表示
    end
```
```mermaid
stateDiagram-v2

[*] --> ホーム

ホーム --> 日課追加 : 追加
日課追加 --> ホーム : 保存
日課追加 --> 日課追加 : エラー

ホーム --> 日課編集 : 編集
日課編集 --> ホーム : 保存

ホーム --> 記録入力 : 記録
記録入力 --> ホーム : 保存
記録入力 --> 記録入力 : エラー

ホーム --> 目標設定 : 目標
目標設定 --> ホーム : 保存

ホーム --> グラフ : 表示
グラフ --> グラフ : 期間変更
グラフ --> ホーム : 戻る

ホーム --> 削除確認 : 削除
削除確認 --> ホーム : OK
削除確認 --> ホーム : Cancel

ホーム --> [*]
```

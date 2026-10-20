# AMANEQ側だけのSiTCP起動対策を短縮する追試（2026-10-19）

**Language: [English](README.md) | 日本語**

## 最終結果

今回、ソースからビルドして両基板で確認できた最小の採用候補は **F402**。AMANEQの`hdl/toplevel.vhd`だけで、**機能上は3行追加＋既存1行変更**、コメント・空行を含むGit差分は **追加6行／削除1行（正味5行増）**。[適用する差分](patches/outerreset-functional-f402.patch)、[ファイル全体](source/f402/toplevel.vhd)、[資格確認](evidence/outerreset-f402-independent-review.json)。生成IP内部の起動FSMは変更しない。

問題基板.16は **7/7**、正常基板.17は **6/6**。[全コホート集計](evidence/outerreset-cohort-summary-final.json)、[終了後のキャプチャー照合](evidence/outerreset-packets-final.json)。これは今回調べた候補の中での最小で、すべての回路の数学的最小を証明したものではない。

物理的な引き金は引き続き未確定。前回の[受信回復クロックとPMA/CDRの調査](../deep-reset-20261018/README.ja.md)と、今回の上位リセット比較を区別する。

F401の同一配置・配線比較では、問題基板が有効3/3→無効0/3→初期リセット延長0/3→再び有効3/3と切り替わった。延長版と有効版の最後の解除エッジをそろえているため、この比較は単なる解除時刻の遅延より、起動を一度試した後のEthernet再初期化の効果を支持する。[比較の証拠](evidence/outerreset-f401-causal-reversal.json)、[比較前に記録した仮説](evidence/outerreset-causal-hypotheses-before-hold-raw.json)。物理原因や将来の故障率を一意に決める結果ではない。

### 全起動比較

| 候補／条件 | 基板 | 成功／試行 | OFF指定秒 |
|---|---|---:|---|
| [f401 / enabled](evidence/outerreset-cohort-outerf40116a.json) | 192.168.10.16 | 3/3 | 5, 5, 5 |
| [f401 / enabled](evidence/outerreset-cohort-outerf40116back.json) | 192.168.10.16 | 3/3 | 5, 5, 5 |
| [f401 / bypass](evidence/outerreset-cohort-outerf40116by.json) | 192.168.10.16 | 0/3 | 5, 5, 5 |
| [f401 / hold](evidence/outerreset-cohort-outerf40116hold.json) | 192.168.10.16 | 0/3 | 5, 5, 5 |
| [f401 / enabled](evidence/outerreset-cohort-outerf40116long.json) | 192.168.10.16 | 3/3 | 30, 120, 600 |
| [f401 / enabled](evidence/outerreset-cohort-outerf40116more.json) | 192.168.10.16 | 18/18 | 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5 |
| [f401 / enabled](evidence/outerreset-cohort-outerf40117a.json) | 192.168.10.17 | 3/3 | 5, 5, 5 |
| [f401 / enabled](evidence/outerreset-cohort-outerf40117more.json) | 192.168.10.17 | 9/9 | 5, 5, 5, 5, 5, 5, 5, 5, 5 |
| [f402 / enabled](evidence/outerreset-cohort-outerf40216a.json) | 192.168.10.16 | 3/3 | 5, 5, 5 |
| [f402 / enabled](evidence/outerreset-cohort-outerf40216backlong.json) | 192.168.10.16 | 4/4 | 5, 30, 120, 600 |
| [f402 / bypass](evidence/outerreset-cohort-outerf40216by.json) | 192.168.10.16 | 0/3 | 5, 5, 5 |
| [f402 / early](evidence/outerreset-cohort-outerf40216raw.json) | 192.168.10.16 | 3/3 | 5, 5, 5 |
| [f402 / enabled](evidence/outerreset-cohort-outerf40217a.json) | 192.168.10.17 | 3/3 | 5, 5, 5 |
| [f402 / enabled](evidence/outerreset-cohort-outerf40217back.json) | 192.168.10.17 | 3/3 | 5, 5, 120 |
| [f402 / early](evidence/outerreset-cohort-outerf40217raw.json) | 192.168.10.17 | 1/3 | 5, 5, 5 |
| [f403 / enabled](evidence/outerreset-cohort-outerf40316a.json) | 192.168.10.16 | 3/3 | 5, 5, 5 |
| [f403 / enabled](evidence/outerreset-cohort-outerf40317a.json) | 192.168.10.17 | 1/3 | 5, 5, 120 |
| [factory / enabled](evidence/outerreset-cohort-outerfact16long.json) | 192.168.10.16 | 0/3 | 30, 120, 600 |
| [factory / enabled](evidence/outerreset-cohort-outerfact16q.json) | 192.168.10.16 | 0/3 | 5, 5, 5 |
| [factory / enabled](evidence/outerreset-cohort-outerfact17long.json) | 192.168.10.17 | 3/3 | 30, 120, 600 |
| [factory / enabled](evidence/outerreset-cohort-outerfact17q.json) | 192.168.10.17 | 3/3 | 5, 5, 5 |

上の標準コホート表とは別に、最初のfactory .16直後プローブ3回は0/3。[記録](evidence/deepreset-native-outerfact16a-cold3.json)。標準factory .16の6回と合わせて0/9。診断用`hold`／`early`を、独立した最小ソース版の検証結果として数えない。

### 連続通信

- [outerreset-soak-f401both.json](evidence/outerreset-soak-f401both.json): 900秒指定、read_only_candidate_soak_completed_both_healthy。各基板のRBCP／TCPの回数と失敗数は記録参照。
- [outerreset-soak-f402both.json](evidence/outerreset-soak-f402both.json): 600秒指定、read_only_candidate_soak_completed_both_healthy。各基板のRBCP／TCPの回数と失敗数は記録参照。

### 適用・再ビルド

ベースコミットは`5ac5ce75944aaec1ab2d4e81588aa9ab19eb7039`。パッチの適用とGitの差分行数は[一時indexを用いた検査](evidence/outerreset-patch-application-check.json)で確認した。通常のAMANEQ cloneで、対応パッチを取得して`git apply outerreset-functional-f402.patch`、`git diff --check`を実行する。既存RstDelayTimerの利用なので新モジュールの登録は不要。

テスト用のバージョン識別子は機能差分と別。[defBusAddressMap.vhd](source/f402/defBusAddressMap.vhd)に保存した。[study build.tcl](source/f402/build.tcl)はVivado2023.2、当時のI/J/Yドライブ割当と以前の検査済みDCPを参照する研究用スクリプトで、任意の新しいcloneにそのまま移すためのものではない。独立再ビルドでは通常のAMANEQビルド手順を使用するか、研究用の参照DCP指定を外し、再度STA／DRC／bus skewを確認する。156.25 MHz用CPLL／XDCの既存設定は引き続き必要。[クロック設定検査](evidence/outerreset-f402-board-clock-audit.json)。

機能1ファイルだけのローカルcommitは[ソースcommit記録](evidence/outerreset-final-source-commit.json)を参照。公開upstreamへのpushは行っていない。

復元・後片付け・検証済みソースのcommitを必須にした[最終整合性検査](evidence/outerreset-local-completion-audit-v2.json)も完了した。旧版の検査記録は、その時点の範囲を保ったまま保存している。

### 最終状態

**.16はF202、.17は元のfactoryへ復元済み**。新たな全16 MiB読戻し、各3回の起動、RBCP／TCP、EEPROM不変、両電源ONを確認。[復元](evidence/outerreset-restoration.json)、[最終状態](evidence/outerreset-final-status.json)、[復元後の連続確認](evidence/outerreset-final-soak-summary.json)、[キャプチャーと一時スリープ抑止の終了](evidence/outerreset-resource-cleanup.json)。生のパケット、EEPROM、Flashイメージ、DCP、電源認証情報は公開記録へコピーしていない。

### 1行変更F403は不採用

`reset => pwr_on_reset`を`reset => raw_pwr_on_reset`へ変えるだけのF403も、タイマーを除いた独立ソースからビルドし、STA／DRC／初期値／実配線／全Flash読戻しを通して試験した。結果は問題基板.16が **3/3**、正常基板.17が **1/3**。正常基板にも失敗を発生させたため採用しない。成功した.16だけを見て「1行で解決」と扱わない。[独立した1行差分](patches/outerreset-functional-f403.patch)、[資格確認](evidence/outerreset-f403-independent-review.json)、[全実機結果](evidence/outerreset-cohort-summary-final.json)。

F403の.17初回比較ではOFF指定5秒で2回失敗し、120秒の1回は成功した。この3回だけで長いOFFなら常に正常と結論しない。ARPの実要求・応答は閉じたキャプチャーで照合した。追加のF403長時間試験を続ける代わりに、既に通過したF402と同じ配置の`early`診断を.17でも比較し、その後F402有効版へ戻した。
F402の同じ配置・配線で早期解除のみを使う診断版は、正常基板.17で **1/3**。[記録](evidence/outerreset-cohort-outerf40217raw.json)。早期解除だけの診断版にも失敗があり、今回の両基板へ適用する候補には追加の再初期化を残す。物理的な引き金まで特定した結果ではない。

正常基板.17のF402有効版は初回3/3、早期解除だけは1/3、その後有効版へ戻して3/3（うち120秒OFFを1回）だった。[正常基板の回帰と復帰の証拠](evidence/outerreset-board17-regression-reversal.json)。少数の順序付き比較であり、実電源レールや失敗中のFPGA DONEは測定していない。無応答を一意にCDR故障と決めない。

同一配置・配線の比較はF401／F402の診断版に限る。F403は余分なタイマーを除いた別ソースを合成・配置配線しており、F402やfactoryとの配置一致は主張しない。

この探索で両基板の全試行を通過した最小の採用候補を選んだ。1行の案すべてが不可能だという証明ではない。既存RstDelayTimerのreadyOutはdelayRstOutの単なる反転で、別の中間時刻は提供しないため、同じ2信号を組み合わせるだけで有限の追加reset窓を作ることはできない。F402は既存の全体待ち時間を終端に再利用し、独立したタイマーを1個だけ追加している。[既存タイマー出力の確認](evidence/outerreset-existing-timer-output-analysis.json)。

## 実装と試験設計の詳細

**実機試験と最終復元を完了。** 上記の最終結果と証拠を参照。準備・ビルド等のJSONは作成時点の状態を変更せず保存している。

対象は AMANEQ-official/StrLrTdc の `5ac5ce75944aaec1ab2d4e81588aa9ab19eb7039`。2枚を同じスイッチへ接続したまま試験する。.16は問題が出る基板、.17は正常な比較基板。菊水の出力だけで.16、旧スイッチ用ezOutletで.17を操作し、スイッチは常時ON。菊水30 V／1 Aの設定やEEPROMは変更しない。

今回の目的は、生成されたAMD IPのRX起動FSMを編集せず、AMANEQの上位ソース側だけで小さい対策を作って試すこと。従来のF202には専用の114行モジュールと接続がある。前回のF30Bは追加4行／削除3行で75回の起動を確認したが、生成IPの内部を編集するため、今回の条件と区別する。

## 候補と行数の数え方

| 候補 | 実際の差分 | 追加制御 | 意図 |
|---|---:|---|---|
| F401 | 追加9行／削除1行 | 既存RstDelayTimerを2個 | 通常の電源投入待ち後、1秒動かして100 msだけ外部resetを再投入 |
| F402 | 追加6行／削除1行 | 同タイマーを1個 | SYSロック後1秒で再resetし、既存の約2.147秒の電源投入待ちが終わる時に解除 |
| F403 | 追加1行／削除1行（既存1行変更） | なし | Ethernet側をSYSロック後に起動し、SiTCP側の元の待ち時間は維持 |

F401／F402の差分の追加行数には、変更後のreset接続行、コメント1行、空行1行を含む。F401の正味増分は8行、F402は5行。バージョン識別子とビルド・試験スクリプトは別。既存AMANEQの156.25 MHz用CPLL／XDC設定も共通の前提として別記し、新しい起動対策として数えない。新しいHDLモジュールや独立したリセットFSMを追加しない。

F402は単に同じコードを1行に詰めたものではない。既存の電源投入タイマーを再利用し、タイマー1個とリセット用信号・代入を取り除く。無関係な既存信号の流用や、受信成立まで自身をresetし続ける循環は避ける。

## 何をリセットするか

上位 `GbEPcsPma.reset` へ入力する。既存のPCS resetと4段の非同期assert・同期release回路を経由し、既存のTX／RX起動手順を再実行させる。GTXの `RXPMARESET` 端子だけを、別の100 ms回路で直接叩くものではない。生成IPの500 ns待ち、INIT／SOFT_RESET時のGTRXRESET値、受信正常判定ロジックを変更しない。

公開リセットの同期先については、[AMD PG047 v16.2 Resets](https://docs.amd.com/r/16.2-English/pg047-gig-eth-pcs-pma/Resets?contentId=L6jmqD4heKc3zefmU9oeGA)もGT構成で独立クロックへ同期する構成を説明している。[今回の版・実装との照合](evidence/outerreset-manufacturer-reset-crosscheck.json)。待ち時間は今回の試験用に選んだ値で、動作の裏付けは実機比較による。

タイマーはBASE_CLKから生成する独立した125 MHz SYSクロックで進み、GTの独立クロック200 MHzも同じSYSクロック生成器から供給する。異常になっている受信回復クロックや、Ethernetリンクの成立を待ってタイマーを動かす構成ではない。

F401／F402は起動時の一度だけの追加resetで、運用開始後の故障を監視し続ける回路ではない。起動途中には一度リンクを切る可能性がある。後挿しケーブルの実物試験を自動化するポート管理／別スイッチ電源はなく、その試験を実施済みとは扱わない。

## 試験・判定

合成・配置配線後のSTA、bus skew、既知DRCとの比較、生成されたGT HDLの不変確認、タイマーのシミュレーション、実回路のクロック／リセット配線を確認してから書き込む。SPI全16 MiB読戻しで対象基板とイメージを識別する。比較用の有効／無効イメージでは、全プリミティブのLOC／BEL／INITと5種類の物理DCP内部データを照合し、リセット用LUTのINIT以外が同一であることを確認する。

起動成功は、期待したIPとバージョンのRBCP応答、TCP24接続、その5秒後の再確認で判定する。通常の比較では、試験スクリプトによる最初の接続確認を電源ON応答の12秒後まで待つ。ただし、これはネットワーク線上の12秒間の無通信を保証しない。Windows側の背景ARPはその前にも送られる場合がある。失敗を基板の無応答と扱うには、キャプチャー中の実ARP送信・応答の有無も照合する。

元のファームウェアでは、初回の.16は直後から確認して0/3、12秒待って確認して0/3、.17は12秒待って3/3だった。失敗6起動すべてで実ARP要求があり、基板からのARP応答がなかった。その後の長いOFFと新候補の結果は、上記の全試験表を参照。元ファームウェアの.16は長いOFFを加えて計0/9、.17は計6/6だった。

回復しても物理的な根本原因の確定とはしない。前回までの観測は受信回復クロック／PMA-CDRの起動状態への依存を示すが、MGT電源、基準クロックのジッター、欠落エッジ、個別部品のどれが引き金かを一意に識別してはいない。

## 終了条件

最後は.16をF202、.17を元のfactoryへ戻す。新しい全読戻し、各3回の電源再投入、RBCP／TCP、EEPROM不変、両電源ONを確認する。キャプチャーと一時スリープ抑止を終了し、試験で作ったドライブ割当だけを解除する。新候補を通常運用へ自動採用したとは扱わない。

外部入力を使ったTDC精度・校正の検証は、この起動・通信試験には含まれない。

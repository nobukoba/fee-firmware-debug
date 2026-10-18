# 最小リセット変更の追試（2026-10-18午後）

**実機比較・両基板の復元・終了確認まで完了。物理的な根本原因は未確定。**
構成後500nsの待機を保ち、既存回路の再利用で機能HDLの変更量を減らす。

## 実機比較結果

| 順序 | .16のファームウェア | 電源再投入成功 |
|---|---|---|
| 1 | 元factory | 0/3 |
| 2 | F30A：既存待ち定数1行変更 | 1/3 |
| 3 | 元factoryへ戻す | 0/3 |
| 4 | F308：最小化したPMA追加 | 3/3 |

正常側.17もF308で3/3回成功。LAN接続・スイッチONのまま、電源OFF/ON後90秒以内に
RBCP・TCP24・バージョン・IPが一致し、5秒後の再確認も成功した場合だけ合格とした。
各書込みは16 MiB全領域の読戻しが期待値と一致している。
F308の.16で成功を確認した時間は約63.7・14.0・14.0秒だった。最初の基板フレームは約58.5秒後。
ホストのARPバックオフや準備待ちの影響を含み、PMAの実パルスは今回観測していないため、
基板単体が1秒で起動することを確認した結果ではない。
[F308の.16試験](evidence/minpma-v2-cohort-pma16a.json)、
[.17回帰試験](evidence/minpma-v2-cohort-pma17a.json)、
[元版への逆比較](evidence/minpma-native-minrev16.json)。

今回実機で確認できた、元の500ns初期化待ちを保つPMA追加候補の最小は
**32行追加／1行削除（新規機能ブロック29行、接続の置換行1行、空行2行）**。
他の実装がさらに短くできないことの証明ではない。

.16を元factoryへ書込み、16 MiBの全領域読戻しが期待値と一致した。
スイッチONのまま電源OFF/ONを3回行い、90秒の通信成立期限では **0/3回成功**。
各起動後にホストからARP要求を8・1・1回観測し、対象MAC/IPからのフレーム・ARP応答は0。
[元factory対照](evidence/minpma-native-minbase16.json)、
[パケットとの照合](evidence/minpma-packets-native-baseline.json)。

3回目の失敗後、構成DONE・EOSは1、CRC・ID・フォールバックの各エラーは0。
約26分後の読取りだけの通信確認も2回ともRBCPタイムアウトだった。
構成レジスターのPLL_LOCKはGTXのCPLL/CDRロックを示すものではない。
[構成状態](evidence/minpma-native-config-status.json)、
[遅延後の通信確認](evidence/minpma-native-late-readonly.json)。

正常側.17のfactory監視は約2時間35分、RBCP 311/311・TCP 32/32成功で終了した。
[監視終了と集計](evidence/minpma-control17-stop-verified.json)。
菊水は.16、ezOutletは.17の電源。ネットワークスイッチは常時ON。EEPROM書込みなし。
今回の起動試験はLAN接続済みで実施。後挿し・ポートOFF/ON・TDC精度・BERは評価していない。

## 小さくした候補

| 候補 | 機能HDLの差分 | 検証状況 |
|---|---|---|
| F308：1クロック領域・共用カウンター | 32行追加／1行削除 | 初回はWNS −0.044nsで不使用。回路を変えず再配置配線しWNS +0.068ns・WHS +0.015nsで適合。.16・.17とも3/3回成功 |
| F309：既存CDR待ちカウンターを利用 | 6行追加／1行削除 | 論理検証成功だがメーカーの初期化手順と競合するため不採用。実機未使用 |
| F30A：既存WAIT_TIME_MAXを100→1000 | 1行置換 | WNS +0.068ns・WHS +0.015ns。全領域照合後、.16は1/3回成功・2/3回失敗 |

初回の不適合イメージは一度も実機に使用していない。再試行は機能HDLを変えず、
既に適合していたF307のDCPを参照して配置配線した。新旧で完全に同じ配置ではない。
したがってF308のこの比較単独でPMAの因果効果を厳密に証明するのではなく、
前回F307の同一配置・物理PMAゲート比較とは分けて扱う。

[F308再配置配線](evidence/minpma-f308-build-v2.json)、
[独立レビュー](evidence/minpma-f308-v2-independent-review.json)。

F308の32行追加には接続の置換行と空行2行を含み、新規機能ブロックは29行。
F309は宣言と既存process内への新規5行、および接続1行の置換。
F308はTXユーザークロック上で、7条件の2段同期化、準備完了後1秒待ち、16クロックのPMAパルス、
単発動作を1つのカウンターで扱う。RXRESETDONEがパルス中に下がってもパルスを完了し、
SOFT_RESET_RXで再許可する。旧104行版のクロック間完了応答・診断状態を省いている。
単にRXRESETDONEとANDしてPMAを出すと、PMA自身がRXRESETDONEを下げた時に
パルスが途中で切れ得るため、パルス開始後の幅をカウンターで保証する。
この追加回路は起動時の単発操作で、通信成立の継続監視や自動再試行は行わない。
既存のRX起動FSMは動作し続けるが、後述の復旧条件の盲点は別に残る。
単に改行を減らすことを最小化とは扱わず、既存の状態・カウンターの再利用を比較する。
バージョン・ビルド手順・比較用ゲート／ILAは、この機能HDL行数には含めない。
[候補状態の確定記録](evidence/minpma-candidate-status-frozen.json)、
[F308差分](f308-prototype.patch)、[F309差分](f309-prototype.patch)。

F309は初回RXRESETDONEより前にPMAリセットを出す。UG476では初期化中の個別リセットを
RXRESETDONEが上がるまでLowに保つため、論理検証が通っても採用しない。
[不採用理由](evidence/minpma-f309-design-review.json)、
[AMD UG476](https://docs.amd.com/v/u/en-US/ug476_7Series_Transceivers)。

F30Aは今回1/3回成功に留まり、確実な対策としては不十分。
[実機試験](evidence/resetwidth-cohort-width16a.json)、[1行差分](f30a-native-wait.patch)。

F30Aの定数は、構成後待ちの`STARTUP_DELAY`とは別である。
元のINIT0・SOFT0・STARTUP_DELAY 500nsを保ち、ネイティブRXリセット手順中の最短待機と、
その後のRXユーザークロック待ちに使う定数を変更する。
理想PLLの論理モデルではGTRXRESET保持が515ns→5015nsとなったが、これは実波形ではない。
[F30A論理検証](evidence/f30a-logical-simulation.json)。

既報F304の[2行変更](../minimal-f304.patch)は、GTRXRESETの初期値とSOFT_RESET時の値を1にする別案で、
前回は両基板15/15回成功した。ただし構成後500nsの待ちより前からリセットがHighになり得るため、
その初期条件のメーカー手順への適合性は未確認。今回は500nsの元手順を保つ候補を比較している。
機能HDL以外の共通Vivado 2023.2向けIP再生成補正・クロック制約・バージョン・ビルド手順は別に必要で、
プロジェクト全体の差分が1行・32行という意味ではない。

## 原因について今回わかったこと

以前の不良起動3回の凍結済み状態イベント記録を、ハッシュ一致を確認して再解析した。
起動直後のMONITOR_DATA_VALID／FSM_DONEの記録範囲は約131〜136µs。
その中で、監視状態から完了状態へ戻る区間は最大585・595・585nsだった。
一方、再リセットには連続100µsの不良が必要で、正常扱いへ戻るとタイマーが初期化される。

**監視が停止するのではなく、短い同期不良の繰返しが連続不良の閾値に届かない**
という復旧上の盲点を支持する。通常のPRBS選択000ではエラー時の再試行は有効であり、
単にDONT_RESET_ON_DATA_ERRORが1固定だからという説明ではない。
DATA_VALIDはPCSの同期状態bit1であり、Auto-NegotiationやIP通信の成功そのものではない。
[再解析と限界](evidence/minpma-fsm-recovery-analysis.json)、
[AMD PG047のステータス定義](https://docs.amd.com/r/en-US/pg047-gig-eth-pcs-pma/Configuration-and-Status-Vectors)。

この記録は90秒全期間の連続波形ではない。PMA後のログには直前の256イベントの再読出しが
含まれていたため、同じ古いブロックを新しい不良として重複計上していない。
受信部が最初に不良状態へ入る基板上の物理原因は未確定。

また以前の実機記録では、PLL待ちを含むRXリセット保持は約31.36〜31.57µsだった。
解除後にCDR待ちタイマーが約50µs進み、さらに約520ns後にRXUSERRDYが上がっていた。
したがってF30Aの結果から、リセット幅だけの効果とは断定できない。
後段のユーザークロック待ちが延びる効果も切り分ける必要がある。
CDR待ちタイマーは実際のCDRロック検出ではない。
[ネイティブ起動順序の再解析](evidence/minpma-native-order-analysis.json)。

不良時とPMAリセット後の平均クロック差は約709ppmだった。一定の周波数ずれと仮定すると、
1UIずれるまで約1.128µsで、実際のMONITOR遷移の中央値1.130〜1.155µsに近い。
繰返し位相が滑って同期を失うモデルとは整合するが、位相・ジッターの直接測定ではなく、
欠落パルスなど別の説明も残る。[周波数と状態周期の比較](evidence/minpma-slip-scale-analysis.json)。

## 証拠の扱い

実機試験前の予想を[事前仮説](evidence/minpma-pretest-hypotheses.json)に保存した。
パケットは完全なPCAPNGブロックだけを切り出した別スナップショットで解析し、
生キャプチャやEEPROM生データ、認証情報は同梱しない。
元ファイルと公開用JSONの変換後ハッシュは[export-manifest.json](export-manifest.json)で区別する。
同じファイル名の確定証拠は上書きしない。

21回の起動窓を[パケットと照合](evidence/minpma-packets-comparison.json)した。
失敗した8回では対象MAC/IPからのフレームが0、成功した13回ではRBCP・TCP応答を確認した。
ホストNICでの観測なので物理線上のAuto-Negotiationやアナログ波形の証拠ではない。

キャプチャーは試験と試験の間に2本へ切り替えた。
[切替記録](evidence/minpma-capture-handoff.json)と[結合検証](evidence/minpma-capture-merge.json)を保存。
最後の元フレームから継続取得確認まで約596秒を保守的な除外区間とし、
21回の起動窓のいずれも交差しないことを検証した。この区間は無通信の待機時間も含み、
実際のキャプチャー停止時間ではない。正確な停止間隔とドロップ数は不明。

## 最終状態

.16は既存F202（0x60C4F202）、.17はfactory（0x60C4020A）へ復元した。
16 MiB全領域読戻しが各基準と一致し、復元後の電源再投入も各3/3回成功。
繰り返しのRBCP・TCP・バージョン・IP確認、EEPROMの元ハッシュ一致、
菊水30V/1Aの設定維持、両電源ONを確認した。
[復元記録](evidence/minpma-restoration.json)、[最終通信・設定確認](evidence/minpma-final-status.json)。

監視・ビルド・書込み・電源試験・キャプチャー・一時スリープ抑止はすべて終了。
dumpcapは明示Ctrl-Cで2回とも終了コード1だったが、各ファイルの読取りと結合後のcapinfos検証は成功。
[終了確認](evidence/minpma-cleanup.json)、[138件のハッシュと状態の完了監査](evidence/minpma-completion-audit.json)、
[結果集約](evidence/minpma-reviewed-outcome.json)。

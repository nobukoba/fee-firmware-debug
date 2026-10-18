# AMANEQ SiTCP 起動不良：追加切り分け（2026-10-18開始）

**調査中の途中記録。最終結果・採用修正ではありません。** 約10時間を目安に継続し、終了時に両基板を元の運用状態へ復元する。

## 第7チェックポイント：CDR保持の陰性結果とホストARPの交絡

起動直後のFSMを記録すると、正常時は一度でDONEへ進むが、失敗2回はMONITORとDONEを90回／91回往復した。DONEの滞在は400～1760 nsだった。この短い正常判定で既存100 µsエラー監視が繰り返し解除される、という論理上の抜け道がある。[波形比較](evidence/deepreset-txpcs-startup-trace-comparison.json)。記録は最初の256イベントに限られ、全起動期間のリセット回数を測ったものではない。

RXCDRHOLDを、実際のRXUSERRDYが上がるまで保持する同一配置の診断版は **.16で0/3** だった。別の失敗起動で5.12 µs／40.96 µsのHOLDを与え、GT入力まで届くことと他の5種類のリセット要求が静止していることを確認したが、異常な回復RXクロックは直らなかった。単純なHOLDを追加する3行の通常ソース案は採用しない。[手動操作](evidence/deepreset-hold-cohort-deephold16m.json)、[起動時保持](evidence/deepreset-hold-cohort-deephold16r.json)、[独立検査](evidence/deepreset-cdrhold-postload-review-v15.json)。これは全てのCDR問題・全ての保持時間を否定する結果ではない。

同じ起動でPMA操作後にRXクロックと新しい受信256ワードは正常化したが、直後の通信検査だけは失敗表示になった。パケットを照合すると、その時間帯にはホストからARPもUDPも送られていなかった。従って、この表示を「PMA後もMACが故障」と解釈できない。その後、同じ起動のまま通信が成功した。[PMA後の受信確認](evidence/deepreset-hold-manual-RX-summary.json)、[送信有無](evidence/deepreset-packet-hold-interim.json)、[後続通信](evidence/deepreset-neighbor-ready16post.json)。

Windowsの対象IPだけにResolveIpNetEntry2を実行する確認を追加した。ただしAPIを呼んでも、実際のARP再試行は約60秒空く場合が残った。API呼び出し回数をパケット送信回数と同一視しない。新しいキャプチャー照合では、元ファームウェア .16 **0/3** とフィルター無効 **1/3** の失敗試験でも、電源ONから遅い時点に実際のARP要求が送られ、応答がなかった。一方、フィルター有効 **3/3** は約63秒後の要求へ即座に応答した。[送受信時刻の照合](evidence/deepreset-packet-fresh-neighbor.json)。12秒待ってから検査した無効版と、直後から検査した有効版には試験方法の差があるため、直後からの無効版も追加比較中。

このホスト側の遅延は通信失敗・復帰時刻の解釈に影響するが、ILAで直接測った異常なRX平均クロックと正常なTXPCS平均クロックの差を説明するものではない。過去の内部PMAループバックも .16 0/3、.17 3/3だった。[過去試験の再照合](evidence/deepreset-prior-loopback-recheck.json)。XADCで読める電源・温度には失敗と対応する大きな変化を見なかったが、MGT専用電源の過渡変動やジッターを測ってはいない。[読出し値](evidence/deepreset-txpcs-sysmon-summary.json)。

確認済み最短は引き続き **追加4行／削除3行、3か所**。さらに短い既存定数1行の1 ms案はビルド中で、まだ実機評価前。

## 第6チェックポイント：異常な平均周波数は受信側の回復クロックへ絞れた

**調査継続中。物理的な部品故障の特定には至っていないが、受信側に絞る新しい実測を得た。**
共通CPLL由来のTXOUTCLKPCSを既存カウンターへ接続した観測用イメージを作り、元のGT入力・設定と全既存セルの配置/BELを保った。[独立確認](evidence/deepreset-txpcs-unified-review.json)。元からあるVIOプローブの分割表示は全13ポートのビット範囲を確認して正規化した。既存観測版に元からある422件の警告と、追加回路の警告を混同しないよう比較した。[検査の停止・修正記録](evidence/deepreset-txpcs-fresh-review-failure.json)。

正常基板 .17 は1/1起動成功し、TXPCS約62.49992 MHz、RX約62.50206 MHz（RX/TXPCS約+34 ppm）だった。問題基板 .16 は同じイメージで1/3起動成功、2/3失敗した。失敗した2回を、それぞれ同じ起動のままPMAリセット前後で比較した。
[集計](evidence/deepreset-txpcs-paired-summary.json)、[解釈と限界](evidence/deepreset-txpcs-interpretation.json)。

| 問題基板 .16 | 共通CPLL由来のTXPCS | 回復RXクロック | RX/TXPCS | RBCP/TCP |
|---|---:|---:|---:|---|
| 正常だった起動 | 約62.49837 MHz | 約62.50036 MHz | 約+32 ppm | 成功 |
| 失敗起動2回 | 約62.49838 MHz | 約62.45603 MHz | 約−678 ppm | 不成立 |
| 各起動でPMAリセット後 | 約62.49838 MHz | 約62.50035 MHz | 約+31 ppm | 回復 |

PMAリセット前後のTXPCS変化は約0.046 ppm／0.025 ppmだった。RXOUTCLKSEL=010が回復RXOUTCLKPMAを選び、TX/RXSYSCLKSEL=00が同じCPLLを選ぶことも物理入力から確認した。クロック経路の根拠は[UG476 Figure3-28 p150、およびp212](https://docs.amd.com/v/u/en-US/ug476_7Series_Transceivers)。

この結果は、**共通PLL全体の平均周波数がずれているという説明より、受信PMA/CDR側の回復クロック経路が不適切な状態へ入るという説明を支持する**。平均値だけではPLLのジッター・電源変動・信号品質・クロック欠落は除外できず、固有の部品や物理的な引き金までは確定しない。PMA操作中の全リセット波形をこの集計では独立に復号しておらず、「純粋にPMAだけの効果」とも断言しない。

次は、他のリセット信号も観測しながらCDRを基準クロックへ保持する実験で、さらに範囲を絞る。確認済みの短い通常ファームウェア修正は引き続き4行追加・3行削除で、3行のCDR保持案はまだ構文確認・準備のみ。

## 第5チェックポイント：1行のクロック待ち案は問題基板で改善せず

**調査継続中。確認済みの短い修正は引き続きF30Bの4行追加・3行削除。**
既存のMMCMロック判定までGTRXRESET解除を待つ[1行置換F30C](patches/deepreset-functional-f30c.patch)は、フルビルドと[独立確認](evidence/deepreset-f30c-independent-review.json)に通った（WNS +0.068 ns、WHS +0.015 ns）。しかし実機では問題基板 .16 が **0/3成功**、正常基板 .17 が **3/3成功**だった。
[問題側](evidence/deepreset-cohort-deepf30c16a.json)、[正常側](evidence/deepreset-cohort-deepf30c17a.json)。この単純な待ち方だけでは解消しない。別配置のビルドであり、クロック時序が物理的原因ではないと一般に証明するものではない。

同一配置のF30Dフィルター有効版は、両基板とも30分の読み出し監視でRBCP 60/60、TCP 6/6、失敗0だった。[監視記録の集計](evidence/deepreset-f30d-soak-summary-v2.json)。監視終了の端末イベントとプロセス不在を確認したが、ツール出力に数値の終了コードがなかったため、その欄はnullとしている。

[対照試験のパケット解析](evidence/deepreset-packet-matched-interim.json)でも、フィルター素通しの失敗3回はARP応答・IPv4応答がなく、有効へ戻した3回は応答した。起動後に最初のARP要求が遅れた事例はPC側ARP負キャッシュの影響を含むため、FPGAの起動所要時間とは扱わない。キャプチャーは調査中で、最終ファイルのハッシュは終了時に別途記録する。

共通PLL由来のTXOUTCLKPCSを測る観測用イメージと、CDRを基準へ合わせる実験を準備中。いずれも、このチェックポイント時点では実機で検証した結果として扱わない。

## 第4チェックポイント：正常判定の修正が効くことを対照試験で確認

**調査継続中。実機検証済みの短い候補はF30Bの機能HDL 4行追加・3行削除。**
問題側 .16 は39/39、正常側 .17 は36/36で、両方とも30秒・120秒・600秒のOFF保持後に各1回成功した。[75回の集計](evidence/deepreset-f30b-75-summary.json)。

配置・配線を同一にし、正常判定を通すLUTのINITだけを変えたF30Dでは、以下の結果を得た。
[対照試験の集計と限界](evidence/deepreset-matched-filter-summary.json)、[独立確認](evidence/deepreset-f30d-independent-review.json)。Vivadoチェックポイント内のPHYSDB_ROUTE、名前対応表、クロックDB、SHAPEがバイト単位で一致し、全プリミティブの配置・INITも判定ゲート以外は一致した。

| 基板 | 条件 | 電源再投入 |
|---|---|---:|
| .16 | 正常判定フィルター有効 | 3/3成功 |
| .16 | フィルター素通し | 0/3成功 |
| .16 | 有効へ戻す | 3/3成功 |
| .17 | 有効・正常基板の確認 | 3/3成功 |

素通し版にも10 µsの待ち時間とカウンター再ロード回路は残る。この条件で、待ち時間延長だけでは改善せず、連続した正常判定を要求するゲートが改善の条件になった。実機のGTリセット波形・再試行回数はこの版では観測していないため、改善を媒介する内部経路を測定済みとはしない。

元のFSMは短い正常判定でもFSM_DONEへ戻り、エラー監視タイマーを消してしまう。失敗起動の状態記録ではFSM_DONE滞在時間は405〜1780 nsだった。代表的な560 ns異常／575 ns正常の波形をメーカーFSMへ与えると、元の500 ns判定を残した**3行追加・2行削除版は監視をすり抜け、10 µs判定を使う4行版は再初期化へ進む**。
[行数削減の反証](evidence/deepreset-filter-threshold-study.json)、[不十分だった3行差分](patches/deepreset-insufficient-three-line-filter.patch)。これは特定の1行削除案を退けた結果で、あらゆる3行以下の修正が不可能という証明ではない。

**500 nsを混同しないこと：** FPGA設定後のSTARTUP_DELAY=500 nsは変更していない。今回10 µsへ変えたWAIT_TIME_MAXは別のカウンターで、元の100サイクルは200 MHz動作では500 nsだった。固定CDR待ち約50 µsも維持する。

正しく1.25 Gbps・20 bit・LPMを設定したGT Wizardで125 MHz／156.25 MHzの対を生成すると、差はCPLL倍率とRX/TX CLK25分周値のみで、受信CDR設定とLPM設定は既存実装と一致した。
[メーカー生成設定との比較](evidence/deepreset-gtwizard-reference-comparison.json)。CLK25分周値の5/7変更は以前の対照試験でも改善しなかった。物理的な受信異常の引き金はまだ確定していない。

別の**1行置換F30Cはフルビルド中・実機未検証**。既存の共通ユーザークロック安定判定までGTRXRESET解除を待つ案で、クロック途中喪失を追加した[全FSMシミュレーション](evidence/deepreset-clockhold-sim-v3-result.json)にも通った。
さらに、CDRをRXUSERRDYまで基準クロックへ合わせる[3行追加・1行削除案](patches/deepreset-readyhold-proposal.patch)も準備したが、こちらは[構文確認のみ](evidence/deepreset-readyhold-hypothesis.json)である。PMAリセットとは別の操作で、現時点で採用を勧めるものではない。

以下は過去の時点の途中記録。

## 21:40 JST時点の途中結果

**調査継続中。現時点の実機成功候補は4行追加・3行削除のF30Bで、問題側 .16 は39/39、正常側 .17 は33/33。**
[集計と限界](evidence/deepreset-f30b-72-summary.json)。.16 は30秒・120秒・600秒のOFF保持でも各1回成功した。追加の通信監視は .16 が15分でRBCP30/30・TCP3/3、.17 が20分でRBCP40/40・TCP4/4、失敗0。長期のTDCデータ品質を保証する検証ではない。

.16 を元のfactoryへ戻すと0/3失敗し、F30Bへ戻すと3/3成功した。
[元に戻した対照](evidence/deepreset-native-deepfactory16r1.json)、[候補へ戻した結果](evidence/deepreset-cohort-deepf30b16r1.json)。
[パケットの途中集計](evidence/deepreset-packet-interim.json)でもfactoryの失敗3回にはARP応答・基板由来IPv4応答がなく、F30Bへ戻した後は同じ基板MACからRBCP/TCP応答を確認した。ホスト側キャプチャーだけではPHY・PLL・CDR内部やアナログ電源の原因は決められない。

比較用F30Dは初回の配線後STAでTDC側2か所のホールド違反（最悪-0.107 ns）が見つかったため、実機には使わず物理的な修正を行う。資格を満たした配置・配線から判定有効／素通しの2版を作り、10 µsの待ち時間延長だけで効くかを調べる予定。

別の**1行置換候補F30Cは、現時点ではシミュレーションのみ・実機未検証**。
[差分](deepreset-functional-f30c.patch)、[仮説と適用条件](evidence/deepreset-clockhold-hypothesis.json)、[全FSMシミュレーション](evidence/deepreset-clockhold-sim-v2-result.json)。最初のGTRXRESET解除が共通ユーザークロックのロックより36.060 µs先行していたため、既存の安定判定まで受信リセットを維持する案である。これをメーカー手順違反や物理的な根本原因の証明とは扱わない。

以下はそれぞれの時点の途中記録。

## 19:55 JST時点の途中結果

**F30Bは問題の .16 で電源再投入3/3成功。まだ採用確定・長期検証完了ではない。** 4行追加・3行削除を保持し、16 MiB全Flash読戻しが一致した。RBCPでIP・版を読み、TCP接続と5秒後の再確認を含めて成功判定した。
[実機コホート](evidence/deepreset-cohort-deepf30b16a.json)、[ビルド独立確認](evidence/deepreset-f30b-independent-review.json)。最終STAはWNS+0.073 ns、WHS+0.009 ns。正常 .17 の同じ版での試験と、待ち時間を共通にした判定ゲートの対照試験を続ける。

正常 .17 のfactory監視は約100分、RBCP201/201・TCP21/21、失敗0で終了した。[対照監視](evidence/deepreset-control17-stop-verified.json)。

同じnative失敗起動では32分後も受信周波数のずれが残った。さらに既存RAM時刻カウンターを5分間測定し、基板内SYS時刻で読み出し遅延を挟んだ結果、受信RXOUTCLKは基準由来ユーザークロックより約583〜729 ppm遅かった。[周波数の解釈](evidence/deepreset-tx-meter-interpretation.json)。
**測った送信ユーザークロックはCPLL出力そのものではない。** TXOUTCLKSEL=100は基準クロック/2を選ぶため、この結果でCPLL内部を正常と断定しない。CDRHOLD比較はオフライン生成中で実機未検証。物理的な起動異常の引き金はまだ確定していない。

以下の「ビルド中」「未確認」は初回チェックポイント時点の記録であり、F30Bの現在の実績は上記を参照。

## 今回確認したこと

問題の .16 へ既存の検証済み F104 周波数観測イメージを書込み、全Flash読戻しを確認した。ネットワークスイッチONで電源を再投入すると起動失敗を再現した。
その同じ失敗状態に対して、追加のリセット・電源操作を行わず、約0・5・10分後に周波数を測定した。3回とも通信不能で、受信クロック平均は約62.456 MHz、受信/基準比は約0.399729だった。正常相当の比0.4付近へ自然復帰していない。
これは**1回の失敗起動を3回観測した結果**であり、独立した電源再投入3回ではない。平均周波数だけでジッターや基板のどの部品が原因かは判定できない。

[観測結果](evidence/deepreset-native-persistence-analysis.json)。通常動作する .17 はfactoryのまま別途通信監視中。

## 短い修正案と未検証事項

- **F30B：4行追加・3行削除、3か所変更。** 既存の待ちカウンターを再利用し、同期が10 µs続くまで復帰扱いにしない。短い同期回復で既存100 µs異常監視が解除され続ける可能性を調べる。500 nsの初期待ちとリセット初期値0は保持し、新しいPMAパルスタイマーを追加しない。
- デジタルシミュレーションでは、正常起動、短い異常、断続的な同期、長い異常、DONT_RESET_ON_DATA_ERROR、SOFT_RESETを確認した。PLL/CDRは理想化しており、**実機効果は未確認、ビルド中**。
- WAIT_TIME_MAXの変更は初期のリセット保持とユーザークロック待ちも延ばす。効いても同期資格判定だけの効果とは断定できず、対照試験が必要。
- **CDRHOLD：1行接続案の仮説。** GTXの文書化されたRXCDRHOLDをGTRXRESETに連動させる案と、起動後に短く操作する診断案を準備中。配置・配線を同じにした無効対照と比較し、他の物理リセット入力が動いていないかも確認する。**まだ実機未検証**。

[F30Bの具体的差分](patches/deepreset-functional-f30b.patch)、[F30Bシミュレーション](evidence/f30b-simulation.json)、[CDRHOLD仮説](evidence/deepreset-cdrhold-hypothesis.json)。

RXCDRRESET/RXCDRFREQRESETなど予約端子の強制操作は行わない。[AMD UG476](https://docs.amd.com/v/u/en-US/ug476_7Series_Transceivers)のGTX仕様を使用する。

## 調査条件

ネットワークスイッチは常時ON。.16は菊水電源の出力のみ操作し30 V/1 A設定を維持。.17はezOutletで電源操作する。EEPROM書込みは行わない。終了時は .16=F202、.17=factoryへ復元し、読戻し・各3回起動・通信・EEPROM・両電源ONを確認する。

既存の[前回調査](../minimum-reset-20261018/README.md)のF308（32行追加・1行削除、両基板3/3成功）を比較基準とする。今回の途中結果で前回の結論を置き換えない。

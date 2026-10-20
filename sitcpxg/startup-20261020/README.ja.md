# StrHrTdc SiTCP-XG ネットワーク接続時の起動調査

**Language: [English](README.md) | 日本語**

## 目的と現状

ネットワークスイッチに接続したまま電源を投入したとき、StrHrTdc の SiTCP-XG が正常に通信を開始するかを、起動不良ボードと正常ボードで比較する。HS3 自体の動作調査ではない。

2026-10-20 の初期確認では `.10` は ping と RBCP 読み取りに応答せず、`.11` は両方に応答した。`.11` の `0xFFFFFF08` は `58544350`（SiTCP-XG 識別子）、`0xFFFFFF00` は `C480020A`（StrHrTdcBase v2.A のソース識別値と一致）。`.10` の実行中ファームウェアは未確認。

## 実測結果

既存ファームウェアのまま、ボード電源を 15 秒以上 OFF にして各条件 3 回ずつ、計 12 回測定した。成功条件は、1 秒以上の間隔で SiTCP-XG 識別子の正しい RBCP 応答が 3 回連続すること。

| 条件 | 観測時間 | .10 成功 / 試行 | .11 成功 / 試行 | .11 の成功時の初回応答 |
| --- | --- | --- | --- | --- |
| スイッチ起動済みでボードを投入 | ボード ON 確認後 60 秒 | 0 / 3 | 2 / 3 | 43.720 秒、9.090 秒 |
| ボード投入後 15 秒以上待ってスイッチを投入 | スイッチ ON 確認後 120 秒 | 0 / 3 | 3 / 3 | 16.410 秒、16.410 秒、14.610 秒 |

`.10` は今回のどちらの順序でも通信を再開しなかった。`.11` にも接続済み起動で 1 回の観測時間超過があり、この構成を安定起動と判定することはできない。各 3 回の予備測定で、条件間の観測時間も異なるため、一般的な失敗率や投入順序の因果効果は確定しない。IP 保存内容・ボードの実行イメージ・内部リセット状態の確認が必要。

スイッチ OFF 中は PC の Ethernet が Disconnected、ON 後は Up となった。スイッチ後投入の .10 試験中に .11 の応答も確認した。試験後は両ボードとスイッチが ON、Ethernet が Up、`.11` が応答、`.10` が無応答という状態に復帰した。ファームウェア・IP・ライセンスの書き換えは行っていない。

## 構成

| 対象 | アドレス | 電源 |
| --- | --- | --- |
| 起動不良ボード | 192.168.10.10 | MSNSwitch2 出力 1 |
| 正常ボード（利用者が指定した予定 IP） | 192.168.10.11 | MSNSwitch2 出力 2 |
| MSNSwitch2 | 172.16.207.110 | ボード電源制御 |
| ezOutlet5 | 172.16.207.91 | ネットワークスイッチ電源制御 |

PC の Ethernet は `192.168.10.70/24`、リンクは 1 Gbps。2 台の JTAG 接続先からそれぞれ XC7K160T を確認した。JTAG 接続と IP の対応付けは未実施。認証情報は保存しない。

初期状態では Wi-Fi が `192.168.19.12/24` で、電源制御器への HTTP がタイムアウトした。その後、利用者によるネットワーク切り替えで Wi-Fi が `172.16.207.92/19` となり、両電源制御器に到達できた。MSNSwitch2 は UIS 自動制御が無効、ezOutlet5 は手動制御であることを確認して測定した。調査スクリプトによる PC のネットワーク設定変更は行っていない。

ezOutlet5 の電源操作要求は HTTP 応答がタイムアウトしても実行されるため、要求結果ではなく状態の読み直しで確認した。最初の未完了試験 1 件は別ファイルに記録し、上表の分母から除外した。回復処理も含め、秘密情報は証拠ファイルに保存していない。

## 最新公開ファームウェアとビルド

対象は [AMANEQ-official/StrHrTdcBase](https://github.com/AMANEQ-official/StrHrTdcBase)。調査時の main は `33e3f35dfc43b04672d0bf6b352be2ff33b5579d`（2025-10-14）。最新公開 MCS は v2.A、ソースの `kCurrentVersion` は `C480020A`。基板版ごとに `amaneq-1-strhrtdc-base-v2.A.mcs` と `amaneq-4-strhrtdc-base-v2.A.mcs` がある。基板版は JTAG の FPGA 型番だけでは確定しない。

メザニン用の MznStrHrTdc は別ファームウェアであり、本調査のネットワーク側ビルド対象ではない。StrLrTdc-10G の v2.1 は今回の対象ではない。

公式 README の指定は Vivado 2023.1.1。この PC の Vivado 2023.2 で 13 個の IP 設定を更新し、HDL を変更せずに比較用ビルドを実施した。全体合成・配置配線・ビットストリーム生成まで成功し、`local/StrHrTdcBase/build/StrHrTdcBase.runs/impl_1/toplevel.bit`（6,692,677 bytes）を生成した。

設定されたタイミング制約は達成（WNS 0.119 ns、WHS 0.041 ns）。一方、入力遅延未設定 37 件・出力遅延未設定 35 件があり、合成中には非同期クロックグループのオブジェクト未検出による Critical Warning が 6 件、DRC には SERDES のクロック構成などの警告がある。全ての実機条件を検証したという意味ではない。

**生成物には Vivado 12-1790 の評価ライセンス警告がある。評価用コアは一定時間後に停止するため、この生成物を本番・長時間運転に使用しない。** 実機への書き込みはしておらず、今回の起動測定には使用していない。この警告を、既存実機の起動不良の原因と結び付ける証拠はない。2023.2 の再生成品と公式配布 MCS の同一性も未確認。ソースと生成バイナリは Git 管理外の `local/` に保存し、ビルド結果・ハッシュは証拠 JSON に記録した。

```powershell
# PowerShell 7、fee-firmware-debug のルートで実行
./sitcpxg/startup-20261020/scripts/inspect-network.ps1
./sitcpxg/startup-20261020/scripts/read-sitcpxg.ps1

# 公式プロジェクト生成後、ソース clone のディレクトリで実行
C:/Xilinx/Vivado/2023.2/bin/vivado.bat -mode batch -source ../../sitcpxg/startup-20261020/scripts/build-baseline.tcl
```

## 試験条件と追加調査

| 条件 | ボード投入時のスイッチ | 調べること |
| --- | --- | --- |
| A（各 3 回実施） | 起動・接続済み | 通常のネットワーク接続下での起動 |
| B（各 3 回実施） | 停止、ボード起動後に投入 | 相手側リンク成立の順序による差 |
| C（未実施） | 起動済み、ボードのネットワーク線を外す | ケーブルを後から接続した場合との差 |

測定スクリプトは `scripts/run-connected-cohort.ps1`。既存ファイルを上書きせず、認証情報は PSCredential で受け取る。B は `-Condition switch_after_board -ObservationSeconds 120` を指定する。A は 60 秒観測、B はスイッチ自身の起動を含む 120 秒観測。試行の時間順序と成功条件は `measurement-audit.json` で 12 件とも整合を確認した。

追加調査ではまず `.10` の保存 IP・実行ファームウェア・基板版を確定する。今回の構成には JTAG デバッグコアがなく、内部状態は直接取得できなかった。独立クロックで PCS block lock、QPLL lock、IDELAYCTRL ready、SiTCP リセットを記録する診断回路が次の候補。設定を揃えた後、同じ観測時間で各条件 30 回程度に拡張すると起動成功率を比較しやすい。未割当 IP や電源不備をファームウェアの起動不良と混同しない。

## ソース上の確認事項

上記固定版の `hdl/toplevel.vhd` は `SystemReset` の `masterReset` を 10G PCS/PMA の reset に接続する。`hdl/common/sitcp/SystemReset.vhd` の masterReset は外部リセットと MMCM lock に依存し、SiTCP 側の同期リセットは QPLL lock・IDELAYCTRL ready と遅延タイマーに依存する。さらに PCS block lock が外れると、同期化された `rst_from_miku_xgmii` を通じて SiTCP-XG の RSTs がアサートされる。PCS/PMA の resetdone は未接続。これらはソースの観察であり、起動不良の原因と断定しない。

固定サブモジュールの SiTCP-XG コアは v4.0（`33916a82262dabfe5321a7a05802643147b3cef4`）。[公式の履歴](https://github.com/BeeBeansTechnologies/SiTCPXG_Netlist_for_Kintex7/blob/33916a82262dabfe5321a7a05802643147b3cef4/README.ja.md)には ARP 応答と RBCP 応答が重なった際の送信ストール修正が記されている。実機に旧版が入っているか、今回の症状が該当するかは未確認。

## 証拠

- [ネットワーク初期状態](evidence/network.json)
- [SiTCP-XG 識別子の読み取り](evidence/rbcp.json)
- [接続済み起動の 6 試行](evidence/connected-cohort.json)
- [スイッチ後投入の 6 試行](evidence/switch-after-board-cohort.json)
- [測定記録の整合確認](evidence/measurement-audit.json)
- [最終電源状態](evidence/final-power-state.json)
- [JTAG 構成レジスタの読み取り](evidence/config-status.json)
- [ビルド結果・タイミング・生成物ハッシュ](evidence/baseline-build-summary.json)
- [進捗と未検証項目](status.json)

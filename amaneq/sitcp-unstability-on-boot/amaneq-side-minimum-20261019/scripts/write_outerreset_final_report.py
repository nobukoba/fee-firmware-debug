"""Prepare final Japanese study prose from completed evidence; review before publishing."""
import argparse,datetime,hashlib,json
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--candidate',choices=['f401','f402','f403'],required=True);a=ap.parse_args()
def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
out=Path('outerreset-result-selection.json');doc=Path('outerreset-study-final.md');assert not out.exists() and not doc.exists()
assert load('outerreset-restoration.json')['phase']=='both_restored_full_readback_cold3_network_EEPROM_verified_power_on'
assert load('outerreset-resource-cleanup.json')['phase']=='capture_closed_sleep_inhibition_released_no_workers'
summary=load('outerreset-cohort-summary-final.json');assert summary['phase']=='all_completed_outerreset_cohorts_checked'
reviewpath=Path('outerreset-'+a.candidate+'-independent-review.json');review=load(reviewpath);assert review['phase']=='independent_review_passed_ready_for_hardware'
selected=[c for c in summary['cases'] if c['candidate']==a.candidate and c['variant']=='enabled'];counts={}
for host in ['192.168.10.16','192.168.10.17']:
 cases=[c for c in selected if c['host']==host];assert cases and all(c['successes']==c['trials'] for c in cases)
 counts[host]={'successes':sum(c['successes'] for c in cases),'trials':sum(c['trials'] for c in cases),'OFF_seconds_tested':sorted({s for c in cases for s in c['off_seconds']})};assert counts[host]['trials']>=3
patch=Path('outerreset-functional-'+a.candidate+'.patch');added=[line[1:] for line in patch.read_text().splitlines() if line.startswith('+') and not line.startswith('+++')];functional=sum(bool(line.strip()) and not line.lstrip().startswith('--') for line in added);assert review['functional_deleted_lines']==1
sources=[Path(__file__),Path('outerreset-cohort-summary-final.json'),reviewpath,patch,Path('outerreset-restoration.json'),Path('outerreset-resource-cleanup.json'),Path('outerreset-packets-final.json')]
selection={'created':datetime.datetime.now().isoformat(),'phase':'final_results_reviewed_after_restoration','selected_candidate':a.candidate,'functional_file':'hdl/toplevel.vhd','git_added_lines':review['functional_added_lines'],'git_deleted_lines':1,'functional_new_lines':functional-1,'existing_lines_replaced':1,'counts':counts,'goal_started_JST':'2026-10-19T05:05:02','finished_records_JST':datetime.datetime.now().isoformat(),'physical_initiating_cause':'unresolved; prior evidence localizes RX recovered-clock/PMA-CDR startup state','source_sha256':{str(p):sha(p) for p in sources},'limits':['Minimum among evaluated qualified source candidates, not a mathematical global minimum.','Diagnostic hold/early LUT controls retain timer logic and do not count as independent shorter production source builds.','Current two boards and connected-switch topology; no automated cable-late physical trial.','External-input TDC accuracy/calibration not tested.','Restored16F202/17factory; candidate not left as operational firmware.']}
shorter=[c for c in summary['cases'] if c['candidate']=='f403']
if a.candidate!='f403' and shorter:
 assert any(c['successes']<c['trials'] for c in shorter)
 selection['rejected_shorter_source_candidate']={'candidate':'f403','existing_lines_replaced':1,'reason':'Cold-start failure observed on healthy comparison board; not adopted.','totals':{h:{'successes':sum(c['successes'] for c in shorter if c['host']==h),'trials':sum(c['trials'] for c in shorter if c['host']==h)} for h in ['192.168.10.16','192.168.10.17']}}
out.write_text(json.dumps(selection,indent=2))
rows=['| 候補／条件 | 基板 | 成功／試行 | OFF指定秒 |','|---|---|---:|---|']
for c in summary['cases']:
 rows.append(f"| [{c['candidate']} / {c['variant']}](evidence/{Path(c['report']).name}) | {c['host']} | {c['successes']}/{c['trials']} | {', '.join(map(str,c['off_seconds']))} |")
soaks=[]
for p in sorted(Path('.').glob('outerreset-soak-*.json')):
 s=load(p);soaks.append(f"- [{p.name}](evidence/{p.name}): {s['requested_seconds']}秒指定、{s['phase']}。各基板のRBCP／TCPの回数と失敗数は記録参照。")
body=Path('outerreset-study-draft.md').read_text(encoding='utf-8')
body=body.replace('**調査中の草稿。実機で有効な修正が確定したという記録ではない。**','**実機試験と最終復元を完了。** 下記の最終結果と証拠を参照。準備・ビルド等のJSONは作成時点の状態を変更せず保存している。')
body=body.replace('長いOFFや新候補の結果は、完了後に追記する。','その後の長いOFFと新候補の結果は、以下の全試験表を参照。元ファームウェアの.16は長いOFFを加えて計0/9、.17は計6/6だった。')
head=f'''\n## 最終結果\n\n今回、ソースからビルドして両基板で確認できた最小の採用候補は **{a.candidate.upper()}**。AMANEQの`hdl/toplevel.vhd`だけで、**機能上は{functional-1}行追加＋既存1行変更**、コメント・空行を含むGit差分は **追加{review['functional_added_lines']}行／削除1行（正味{review['functional_added_lines']-1}行増）**。[適用する差分](patches/{patch.name})、[ファイル全体](source/{a.candidate}/toplevel.vhd)、[資格確認](evidence/{reviewpath.name})。生成IP内部の起動FSMは変更しない。\n\n問題基板.16は **{counts['192.168.10.16']['successes']}/{counts['192.168.10.16']['trials']}**、正常基板.17は **{counts['192.168.10.17']['successes']}/{counts['192.168.10.17']['trials']}**。[全コホート集計](evidence/outerreset-cohort-summary-final.json)、[終了後のキャプチャー照合](evidence/outerreset-packets-final.json)。これは今回調べた候補の中での最小で、すべての回路の数学的最小を証明したものではない。\n\n物理的な引き金は引き続き未確定。前回の[受信回復クロックとPMA/CDRの調査](../deep-reset-20261018/)と、今回の上位リセット比較を区別する。\n\nF401の同一配置・配線比較では、問題基板が有効3/3→無効0/3→初期リセット延長0/3→再び有効3/3と切り替わった。延長版と有効版の最後の解除エッジをそろえているため、この比較は単なる解除時刻の遅延より、起動を一度試した後のEthernet再初期化の効果を支持する。[比較の証拠](evidence/outerreset-f401-causal-reversal.json)、[比較前に記録した仮説](evidence/outerreset-causal-hypotheses-before-hold-raw.json)。物理原因や将来の故障率を一意に決める結果ではない。\n\n### 全起動比較\n\n{chr(10).join(rows)}\n\n上の標準コホート表とは別に、最初のfactory .16直後プローブ3回は0/3。[記録](evidence/deepreset-native-outerfact16a-cold3.json)。標準factory .16の6回と合わせて0/9。診断用`hold`／`early`を、独立した最小ソース版の検証結果として数えない。\n\n### 連続通信\n\n{chr(10).join(soaks) if soaks else '新候補の独立した連続通信コホートは実施していない。起動ごとの再確認と最終復元後の連続確認は別記録を参照。'}\n\n### 適用・再ビルド\n\nベースコミットは`5ac5ce75944aaec1ab2d4e81588aa9ab19eb7039`。パッチの適用とGitの差分行数は[一時indexを用いた検査](evidence/outerreset-patch-application-check.json)で確認した。通常のAMANEQ cloneで、対応パッチを取得して`git apply {patch.name}`、`git diff --check`を実行する。既存RstDelayTimerの利用なので新モジュールの登録は不要。\n\nテスト用のバージョン識別子は機能差分と別。[defBusAddressMap.vhd](source/{a.candidate}/defBusAddressMap.vhd)に保存した。[study build.tcl](source/{a.candidate}/build.tcl)はVivado2023.2、当時のI/J/Yドライブ割当と以前の検査済みDCPを参照する研究用スクリプトで、任意の新しいcloneにそのまま移すためのものではない。独立再ビルドでは通常のAMANEQビルド手順を使用するか、研究用の参照DCP指定を外し、再度STA／DRC／bus skewを確認する。156.25 MHz用CPLL／XDCの既存設定は引き続き必要。[クロック設定検査](evidence/outerreset-{a.candidate}-board-clock-audit.json)。\n\n機能1ファイルだけのローカルcommitは[ソースcommit記録](evidence/outerreset-final-source-commit.json)を参照。公開upstreamへのpushは行っていない。\n\n### 最終状態\n\n**.16はF202、.17は元のfactoryへ復元済み**。新たな全16 MiB読戻し、各3回の起動、RBCP／TCP、EEPROM不変、両電源ONを確認。[復元](evidence/outerreset-restoration.json)、[最終状態](evidence/outerreset-final-status.json)、[復元後の連続確認](evidence/outerreset-final-soak-summary.json)、[キャプチャーと一時スリープ抑止の終了](evidence/outerreset-resource-cleanup.json)。生のパケット、EEPROM、Flashイメージ、DCP、電源認証情報は公開記録へコピーしていない。\n'''
body=body.replace('どちらも起動時の一度だけの追加resetで、','F401／F402は起動時の一度だけの追加resetで、')
f403_cases=[c for c in summary['cases'] if c['candidate']=='f403']
if f403_cases:
 body=body.replace('| F402 | 追加6行／削除1行 | 同タイマーを1個 | SYSロック後1秒で再resetし、既存の約2.147秒の電源投入待ちが終わる時に解除 |','| F402 | 追加6行／削除1行 | 同タイマーを1個 | SYSロック後1秒で再resetし、既存の約2.147秒の電源投入待ちが終わる時に解除 |\n| F403 | 追加1行／削除1行（既存1行変更） | なし | Ethernet側をSYSロック後に起動し、SiTCP側の元の待ち時間は維持 |')
 if a.candidate!='f403':
  fc={h:(sum(c['successes'] for c in f403_cases if c['host']==h),sum(c['trials'] for c in f403_cases if c['host']==h)) for h in ['192.168.10.16','192.168.10.17']}
  assert any(ok<total for ok,total in fc.values())
  head+=f'''\n### 1行変更F403は不採用\n\n`reset => pwr_on_reset`を`reset => raw_pwr_on_reset`へ変えるだけのF403も、タイマーを除いた独立ソースからビルドし、STA／DRC／初期値／実配線／全Flash読戻しを通して試験した。結果は問題基板.16が **{fc['192.168.10.16'][0]}/{fc['192.168.10.16'][1]}**、正常基板.17が **{fc['192.168.10.17'][0]}/{fc['192.168.10.17'][1]}**。正常基板にも失敗を発生させたため採用しない。成功した.16だけを見て「1行で解決」と扱わない。[独立した1行差分](patches/outerreset-functional-f403.patch)、[資格確認](evidence/outerreset-f403-independent-review.json)、[全実機結果](evidence/outerreset-cohort-summary-final.json)。\n\nF403の.17初回比較ではOFF指定5秒で2回失敗し、120秒の1回は成功した。この3回だけで長いOFFなら常に正常と結論しない。ARPの実要求・応答は閉じたキャプチャーで照合した。追加のF403長時間試験を続ける代わりに、既に通過したF402と同じ配置の`early`診断を.17でも比較し、その後F402有効版へ戻した。\n'''
  ec=[c for c in summary['cases'] if c['candidate']=='f402' and c['variant']=='early' and c['host']=='192.168.10.17']
  if ec:
   eok=sum(c['successes'] for c in ec);etotal=sum(c['trials'] for c in ec)
   head+=f'F402の同じ配置・配線で早期解除のみを使う診断版は、正常基板.17で **{eok}/{etotal}**。[記録](evidence/'+Path(ec[0]['report']).name+')。'
   head+=('余分なタイマーを残す診断版の成功を、タイマーを取り除いた1行ソースの成功と同一視できない。\n' if eok==etotal else '早期解除だけの診断版にも失敗があり、今回の両基板へ適用する候補には追加の再初期化を残す。物理的な引き金まで特定した結果ではない。\n')
  head+='\n正常基板.17のF402有効版は初回3/3、早期解除だけは1/3、その後有効版へ戻して3/3（うち120秒OFFを1回）だった。[正常基板の回帰と復帰の証拠](evidence/outerreset-board17-regression-reversal.json)。少数の順序付き比較であり、実電源レールや失敗中のFPGA DONEは測定していない。無応答を一意にCDR故障と決めない。\n'
  head+='\n同一配置・配線の比較はF401／F402の診断版に限る。F403は余分なタイマーを除いた別ソースを合成・配置配線しており、F402やfactoryとの配置一致は主張しない。\n'
  head+='\nこの探索で両基板の全試行を通過した最小の採用候補を選んだ。1行の案すべてが不可能だという証明ではない。既存RstDelayTimerのreadyOutはdelayRstOutの単なる反転で、別の中間時刻は提供しないため、同じ2信号を組み合わせるだけで有限の追加reset窓を作ることはできない。F402は既存の全体待ち時間を終端に再利用し、独立したタイマーを1個だけ追加している。[既存タイマー出力の確認](evidence/outerreset-existing-timer-output-analysis.json)。\n'
if a.candidate=='f403':
 head=head.replace('機能上は0行追加＋既存1行変更','既存1行の変更のみ（タイマー・FSM追加なし）')
 head=head.replace('evidence/outerreset-patch-application-check.json','evidence/outerreset-f403-patch-application-check.json')
 head=head.replace('既存RstDelayTimerの利用なので新モジュールの登録は不要。','タイマーや新モジュールの追加はない。')
 head=head.replace('当時のI/J/Yドライブ割当と以前の検査済みDCP','当時のJ/Kドライブ割当と検査済みF402のIP生成物・DCP')
 head+='\n### 1行候補F403の意味と独立検証\n\n`GbEPcsPma.reset`を`pwr_on_reset`から`raw_pwr_on_reset`へ変更する。SYSクロック生成器のLOCKEDが成立するとEthernetの既存初期化を開始し、SiTCP側は既存の約2.147秒の電源投入resetを維持する。追加の再reset、PMA直接パルス、監視回路、タイマーはない。F402の`early`診断は余分なタイマーを残すため、それだけを1行ソースの検証とはせず、F403を独立にビルドして両基板で試験した。\n\nF403はVivado `save_project_as`で変更のない検査済みIP生成物を引き継ぎ、上位ソースの合成と配置配線を再実行した。全IPを新規生成し直したという意味ではない。コンパイル対象のtop／バージョンが新ソースであること、その他HDLがクリーンな固定版と同じこと、生成GT内部13ファイルが未変更であることを確認した。実DCPでは公開resetの4段同期器の入力がSYS LOCKEDの反転で駆動され、追加タイマーがないことを確認した。F403と元版との配置配線一致は主張しない。同一配置・配線の比較はF401／F402の診断版に限る。\n'
 body=body.replace('どちらも起動時の一度だけの追加resetで、','F401／F402は起動時の一度だけの追加resetで、')
 head+='\n既存RX起動FSMはSOFT_RESET保持中にINITへ戻り、`GTRXRESET=0`にする。公開reset解除後、既存の約500 ns待ちを経てASSERT_ALL_RESETSへ進み、そこで`GTRXRESET=1`になる。したがって今回の1行変更は、GTXを単にresetしなくするものではなく、既存の実リセット手順を早く開始させる。TX側も同様。このソース上の事実は[確認記録](evidence/outerreset-native-reset-sequence-analysis.json)を参照。長いINIT滞在中の受信初期状態への依存という説明は観測と整合するが、電源波形やアナログ部品まで確定した原因ではない。\n'
 head+='\nF402では同じ配置・配線のまま、早期解除のみ3/3、追加再resetあり3/3、元のPORへ戻す無効版0/3だった。[同一配置での比較](evidence/outerreset-f402-causal-contrast.json)。この結果から「追加再reset自体が常に必須」という仮説は狭められ、初期化開始時刻を前へ移す方法も有効な候補になった。F403の独立ソース試験回数には、これら診断版の回数を合算していない。\n'
title,rest=body.split('\n',1);doc.write_text(title+'\n'+head+'\n## 実装と試験設計の詳細\n'+rest,encoding='utf-8');print(json.dumps({'selected':a.candidate,'counts':counts,'functional_new_lines':functional-1,'replaced_lines':1}))

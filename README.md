# BNPL CLIPS Expert System

This prototype integrates the agreed BNPL rules with Python through CLIPSPy.

## 浏览器前端

安装依赖后，在 PyCharm 中右键运行 `web_app.py`，或在项目目录运行：

```bash
python web_app.py
```

然后在浏览器打开 `http://127.0.0.1:8765`。页面提供四类虚构示例用户，按步骤填写并在确认页修改资料；提交后展示审批额度、规则解释和目标额度诊断。本地运行默认仅监听本机，程序不保存申请记录。若 8765 端口已被占用，可用 `python web_app.py --port 8766`，再打开对应端口。

前端使用 Python 标准库提供本地网页服务；除了原有的 `clipspy`，不需要再安装 Web 框架。直接双击 `static/index.html` 无法调用规则接口，必须先启动 `web_app.py`。

## 云端公开演示

项目包含 `render.yaml`、`.python-version` 和 `/healthz` 健康检查，已准备好作为 Render Web Service 部署。具体步骤见 [DEPLOYMENT.md](DEPLOYMENT.md)。目前尚未发布到公网；需要由项目成员连接 Git 仓库并在 Render 创建服务。公开展示只可使用虚构资料，切勿输入真实个人信用信息。

## Setup

Create a virtual environment and install the dependency:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run the example

```bash
python bnpl_expert.py
```

To run a different JSON file:

```bash
python bnpl_expert.py my_applicant.json
```

To see the evidence cap in action, run
`python bnpl_expert.py example_sparse_new_applicant.json`.

The command prints a JSON decision containing:

- application or limit-review branch;
- final decision and approved limit;
- combined certainty factor;
- raw CF sum and applicable positive CF maximum;
- new-applicant evidence coverage, CF-based limit, and evidence tier cap;
- hard decision, when one is triggered;
- every triggered soft rule and its explanation;
- derived credit-limit utilisation rate.

## Run tests

```bash
python -m unittest discover -s tests -v
```

## Missing values

Use JSON `null` for missing optional values. A missing optional value is not
asserted into CLIPS, so its contribution is zero. New applicants must set both
`current_credit_limit` and `available_credit_limit` to `null`.

## CF calculation

The final CF is `max(0, sum of triggered soft-rule CFs / applicable positive
CF maximum)`. The denominator includes the highest positive CF of each
applicable group whose input field has a value; negative rules do not add to
the denominator. A missing field adds nothing to either side. A new applicant
does not use repayment fulfilment, consecutive repayments, or credit-limit
utilisation. With all inputs available, the maximum is 2.50 for a new applicant
and 4.00 for an existing user. A hard rule skips CF calculation entirely.

Account age from 1 through 5 months is neutral. The SR-05 positive interval is
6 through 11 months.

## New-applicant evidence tier cap

The CF formula and hard/soft rules are unchanged. After the CF-based limit is
found, new applications receive an evidence-coverage cap from CLIPS rules
EC-01 through EC-03. Coverage is the applicant's applicable positive CF maximum
divided by the complete new-applicant positive maximum of 2.50. It measures
availability of the positive soft-rule input groups, not the quality of the
values. Existing-user limit reviews do not receive this cap.

| New-applicant evidence coverage | Maximum limit |
| --- | ---: |
| `< 0.70` | CNY 1,000 |
| `0.70 to < 0.90` | CNY 5,000 |
| `>= 0.90` | CNY 10,000 |

The final limit is the smaller of the CF-based limit and the cap. The cap can
only reduce a limit, never increase it. A hard rule still takes precedence and
sets the limit to zero. These coverage thresholds are project policy choices,
not empirically calibrated credit-risk thresholds. Missing inputs used only by
hard rules, such as `adverse_credit_incidents_6m`, are not part of this coverage
ratio; data availability should be discussed separately before any real use.

## Decision mapping

| Combined CF | Decision | Limit |
| --- | --- | ---: |
| `< 0.40` | Rejected | CNY 0 |
| `0.40 to < 0.60` | Conditional approval | CNY 1,000 |
| `0.60 to < 0.85` | Approved | CNY 5,000 |
| `>= 0.85` | Approved | CNY 10,000 |

Hard rules are evaluated before the CF-based result. Every triggered hard rule
rejects a new applicant or suspends an existing user, setting the limit to zero.

## PyCharm 使用说明

1. 解压 ZIP 后，在 PyCharm 中选择 **Open**，打开解压后的整个项目文件夹（包含 `bnpl_expert.py` 和 `rules` 的文件夹）。
2. 在 **Settings → Project → Python Interpreter** 中选择项目里的 `.venv/bin/python`；如果 ZIP 中没有 `.venv`，在 PyCharm 中新建虚拟环境，然后在底部 **Terminal** 执行 `python -m pip install -r requirements.txt`。安装包叫 `clipspy`，代码导入名叫 `clips`。
3. 右键 `bnpl_expert.py` → **Run**。不填参数时，程序读取同目录的 `example_applicant.json`。
4. 要用自己的数据，复制 `example_applicant.json` 并命名为 `my_applicant.json`，只修改其中的值。然后进入 **Run → Edit Configurations**，在 **Script parameters** 填 `my_applicant.json`；**Working directory** 选择项目文件夹。
5. 也可以直接在 PyCharm 的 Terminal 运行 `python bnpl_expert.py my_applicant.json`。

JSON 注意事项：布尔值写 `true`/`false`；缺失数据写 `null`，不要写字符串 `"无"`；枚举值如 `"Credit"`、`"Stable"` 要加双引号。履约率用 0–1，例如 98% 写 `0.98`。新申请人把 `current_credit_limit` 和 `available_credit_limit` 都写成 `null`；已有用户两项都写数字，单位是人民币元。`external_overdue_record` 的字符串 `"None"` 表示确认没有外部逾期，JSON `null` 表示没有取得该字段的数据。

## 目标驱动反向诊断

单独运行 `backward_diagnosis.py`，不传参数会读取 `example_diagnosis_applicant.json`，检查10,000元目标：

```bash
python backward_diagnosis.py
python backward_diagnosis.py my_applicant.json --target 5000
```

PyCharm 中可直接右键运行该文件。使用自己的资料时，在 **Run → Edit Configurations → Script parameters** 填 `my_applicant.json --target 10000`。

诊断先检查硬规则；如果触发，立即显示阻断原因。否则比较当前CF与目标档位门槛，再对注册时长、完成订单数、连续按时还款次数和额度使用率作**单项条件模拟**。每个模拟都重新运行相同的CLIPS规则，只有实际达到目标额度才标记 `reaches_goal: true`。模拟结果是假设分析，不保证未来审批结果。

新用户若因信息覆盖率封顶而无法达到目标，诊断会返回 `blocked-by-evidence-cap` 和缺失的软规则输入字段。补充真实资料后须重新计算；补齐字段本身不保证提额。

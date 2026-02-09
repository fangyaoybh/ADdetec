import router from '@ohos.router';

interface GeneratedTypeLiteralInterface_1 {
  type: string;
  value: number;
  color: string;
}

interface GeneratedTypeLiteralInterface_2 {
  type: string;
  value: number;
  color: string;
}

@Entry
@Component
struct WeeklyReportPage {
  @State chartData: Array<GeneratedTypeLiteralInterface_1> = [
    {type: '健康', value: 19, color: '#4CAF50'},
    {type: '轻度认知障碍', value: 3, color: '#FF9800'},
    {type: '老年痴呆', value: 0, color: '#F44336'}
  ];

  @State careMessage: string = '今日交流正常，老人情绪稳定。';

  build() {
    Column() {
      // 顶部标题栏
      Row() {
        Image($r('app.media.back_arrow'))
          .width(24)
          .height(24)
          .onClick(() => {
            router.back();
          })

        Text('七日报告')
          .fontSize(20)
          .fontWeight(FontWeight.Bold)
          .fontColor(Color.White)
          .layoutWeight(1)
          .textAlign(TextAlign.Center)
      }
      .width('100%')
      .padding(16)
      .backgroundColor('#007DFF')

      Scroll() {
        Column() {
          // 七日预测结果标题
          Row() {
            Text('老年痴呆七日综合预测结果')
              .fontSize(18)
              .fontWeight(FontWeight.Bold)
              .fontColor('#182431')
              .layoutWeight(1)

            Text('点击查看详细统计')
              .fontSize(12)
              .fontColor('#007DFF')
          }
          .width('100%')
          .margin({ bottom: 30 })

          // 柱状图区域
          Column() {
            Row() {
              ForEach(this.chartData, (item: GeneratedTypeLiteralInterface_2) => {
                // 关键修改：将Column改为垂直反向布局（从下往上排列）
                Column() {
                  Text(item.value.toString())
                    .fontSize(16)
                    .fontWeight(FontWeight.Bold)
                    .fontColor(item.color)
                    // 移除bottom margin，或调整为top margin（根据需求）
                    .margin({ top: 4 }) // 数值在柱子上方，所以用top margin

                  // 柱状图（保持中间位置）
                  Column()
                    .width(40)
                    .height(item.value * 10)
                    .backgroundColor(item.color)
                    .borderRadius(4)

                  Text(item.type)
                    .fontSize(12)
                    .fontColor('#666666')
                    // 移除bottom margin，或调整为top margin（根据需求）
                    .margin({ top: 4 }) // 类型标签在柱子下方，所以用top margin
                }
                .margin({ right: 20 })
                // 关键：设置垂直反向布局（从下往上排列）
              })
            }
            .justifyContent(FlexAlign.Center) // 水平居中
            .alignItems(VerticalAlign.Bottom) // 🔥【核心修改】：让所有柱子在垂直方向底部对齐
            .margin({ bottom: 20 })
          }
          .width('100%')
          .padding(24)
          .backgroundColor(Color.White)
          .borderRadius(12)
          .margin({ bottom: 16 })


        }
        .width('100%')
        .padding(16)
      }
      .layoutWeight(0)
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#F5F5F5')
  }
}
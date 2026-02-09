@Entry @Component
struct AppEntry {
  build() {

  }
}





/*
import router from '@ohos.router';


// 定义Patient类型（接口）
interface Patient {
  id: string;
  name: string;
  age: number;
  status: string;
  statusColor: string;
  bgColor: string;
  lastUpdate: string;
}

@Entry
@Component
struct PatientDetailPage {
  private patientId: string = '';
  @State patient: Patient = this.getPatientData(); // 初始化患者数据

  aboutToAppear() {
    // 获取路由参数中的患者ID
    const params = router.getParams() as Record<string, Object>;
    this.patientId = params?.['patientId'] as string || '';
    this.patient = this.getPatientData(); // 更新患者数据
  }

  build() {
    Column() {
      // 顶部标题栏
      Row() {
        Image($r('app.media.back_arrow'))
          .width(24)
          .height(24)
          .onClick(() => {
            router.back(); // 返回上一页
          });

        Text('患者详情')
          .fontSize(20)
          .fontWeight(FontWeight.Bold)
          .fontColor(Color.White)
          .layoutWeight(1)
          .textAlign(TextAlign.Center);
      }
      .width('100%')
      .padding(16)
      .backgroundColor('#007DFF'); // 标题栏背景色

      Scroll() {
        Column() {
          // 患者基本信息卡片
          this.buildInfoCard('基本信息', () => {
            Column() {
              Row() {
                Text('姓名：')
                  .fontSize(16)
                  .fontColor('#666666')
                  .width(80);
                Text(this.patient.name)
                  .fontSize(16)
                  .fontColor('#182431')
                  .fontWeight(FontWeight.Medium);
              }
              .margin({ bottom: 12 });

              Row() {
                Text('年龄：')
                  .fontSize(16)
                  .fontColor('#666666')
                  .width(80);
                Text(`${this.patient.age}岁`)
                  .fontSize(16)
                  .fontColor('#182431');
              }
              .margin({ bottom: 12 });

              Row() {
                Text('状态：')
                  .fontSize(16)
                  .fontColor('#666666')
                  .width(80);
                Text(this.patient.status)
                  .fontSize(16)
                  .fontColor(this.patient.statusColor)
                  .backgroundColor(this.patient.bgColor)
                  .padding({ left: 8, right: 8, top: 4, bottom: 4 })
                  .borderRadius(4);
              }
            }
          });

          // 健康数据卡片
          this.buildInfoCard('健康数据', () => {
            Column() {
              Row() {
                Text('今日对话次数：')
                  .fontSize(16)
                  .fontColor('#666666')
                  .layoutWeight(1);
                Text('8次')
                  .fontSize(16)
                  .fontColor('#007DFF')
                  .fontWeight(FontWeight.Medium);
              }
              .margin({ bottom: 12 });

              Row() {
                Text('对话时长：')
                  .fontSize(16)
                  .fontColor('#666666')
                  .layoutWeight(1);
                Text('15分钟')
                  .fontSize(16)
                  .fontColor('#007DFF')
                  .fontWeight(FontWeight.Medium);
              }
              .margin({ bottom: 12 });

              Row() {
                Text('最后更新：')
                  .fontSize(16)
                  .fontColor('#666666')
                  .layoutWeight(1);
                Text(this.patient.lastUpdate)
                  .fontSize(16)
                  .fontColor('#666666');
              }
            }
          });

          // 预测结果卡片
          this.buildInfoCard('预测结果', () => {
            Column() {
              Text('今日预测结果良好，认知功能正常。')
                .fontSize(16)
                .fontColor('#182431')
                .lineHeight(24);
            }
          });
        }
        .width('100%')
        .padding(16);
      }
      .layoutWeight(1);
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#F5F5F5');
  }

  // 构建信息卡片的Builder
  @Builder
  buildInfoCard(title: string, content: () => void) {
    Column() {
      Text(title)
        .fontSize(18)
        .fontWeight(FontWeight.Medium)
        .fontColor('#182431')
        .margin({ bottom: 16 })
        .width('100%');

      //content(); // 渲染卡片内容
    }
    .width('100%')
    .padding(16)
    .backgroundColor(Color.White)
    .borderRadius(12)
    .margin({ bottom: 16 });
  }

  // 获取患者数据（模拟数据，实际可从云端获取）
  private getPatientData(): Patient {
    // 模拟患者数据（数组形式，避免索引签名）
    const patients: Patient[] = [
      {
        id: '1',
        name: '王大爷',
        age: 78,
        lastUpdate: '2025/11/24 10:30',
        status: '健康',
        statusColor: '#4CAF50',
        bgColor: '#E8F5E8'
      },
      {
        id: '2',
        name: '李奶奶',
        age: 82,
        lastUpdate: '2025/11/24 09:15',
        status: '轻微认知障碍',
        statusColor: '#FF9800',
        bgColor: '#FFF3E0'
      },
      {
        id: '3',
        name: '张爷爷',
        age: 85,
        lastUpdate: '2025/11/24 11:45',
        status: '老年痴呆',
        statusColor: '#F44336',
        bgColor: '#FFEBEE'
      },
      {
        id: '4',
        name: '赵奶奶',
        age: 79,
        lastUpdate: '2025/11/24 08:20',
        status: '健康',
        statusColor: '#4CAF50',
        bgColor: '#E8F5E8'
      }
    ];

    // 根据patientId查找患者，找不到则返回第一个患者
    return patients.find(patient => patient.id === this.patientId) || patients[0];
  }
  */
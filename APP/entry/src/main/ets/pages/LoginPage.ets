import router from '@ohos.router';


export const Path_Login = 'pages/LoginPage'
@Entry
@Component
struct LoginPage {
  @State identity: string = '';
  @State account: string = '';
  @State password: string = '';
  @State isLogin: boolean = true;
  @State isAgreePolicy: boolean = false;

  build() {
    Column() {
      // ---------- 顶部Logo与标题 ----------
      Column() {
        Stack() {
          Image($r('app.media.logo'))
            .width(80)
            .height(80)
            .objectFit(ImageFit.Contain)
            .margin({ bottom: 8 })
        }
        .alignContent(Alignment.Center) // 正确的对齐属性
        .width('100%')
        .height(100)


        Text('关爱·守护')
          .fontSize(24)
          .fontWeight(FontWeight.Bold)
          .margin({ bottom: 4 })


        Text('统一登录 / 注册')
          .fontSize(14)
          .fontColor(Color.Gray)
          .margin({ bottom: 20 })
      }
      .width('100%')
      .alignItems(HorizontalAlign.Center)

      // ---------- 身份选择区域 ----------
      Column() {
        Text('选择身份')
          .fontSize(18)
          .fontWeight(FontWeight.Medium)
          .fontColor('#182431')
          .margin({ bottom: 16 })
          .width('100%')


        Row() {
          // 子女按钮
          Column() {
            // 图标区域
            Image($r('app.media.child_icon')) // 子女图标
              .width(24)
              .height(24)
              .margin({ bottom: 8 })

            Text('子女')
              .fontSize(16)
              .fontColor(this.identity === '子女' ? '#FFFFFF' : '#007DFF')
          }
          .width('50%')
          .height(70)
          .backgroundColor(this.identity === '子女' ? '#007DFF' : '#F0F7FF')
          .border({
            width: this.identity === '子女' ? 0 : 1,
            color: '#007DFF',
            radius: 12
          })
          .borderRadius(12)
          .justifyContent(FlexAlign.Center)
          .alignItems(HorizontalAlign.Center)
          .onClick(() => {
            this.identity = '子女';
          })
          .margin({ right: 12 })


          // 机构/医生按钮
          Column() {
            // 图标区域
            Image($r('app.media.doctor_icon')) // 医生图标
              .width(24)
              .height(24)
              .margin({ bottom: 8 })

            Text('机构/医生')
              .fontSize(16)
              .fontColor(this.identity === '机构/医生' ? '#FFFFFF' : '#007DFF')
          }
          .width('50%')
          .height(70)
          .backgroundColor(this.identity === '机构/医生' ? '#007DFF' : '#F0F7FF')
          .border({
            width: this.identity === '机构/医生' ? 0 : 1,
            color: '#007DFF',
            radius: 12
          })
          .borderRadius(12)
          .justifyContent(FlexAlign.Center)
          .alignItems(HorizontalAlign.Center)
          .onClick(() => {
            this.identity = '机构/医生';
          })
        }
        .width('100%')
        .height(70)
        .margin({ bottom: 28 })


        // ---------- 账号输入框 ----------
        Column() {
          Text('账号')
            .fontSize(18)
            .fontWeight(FontWeight.Medium)
            .fontColor('#182431')
            .margin({ bottom: 16 })
            .width('100%')

          TextInput({ placeholder: '请输入账号/手机号' })
            .placeholderColor('#999999')
            .placeholderFont({ size: 16 })
            .textAlign(TextAlign.Start)
            .caretColor('#007DFF')
            .onChange((value: string) => {
              this.account = value;
            })
            .border({ width: 1, color: '#E5E5E5', radius: 15 })
            .padding(8)
            .margin({ bottom: 12 })
            .width('100%')

          Text('密码')
            .fontSize(18)
            .fontWeight(FontWeight.Medium)
            .fontColor('#182431')
            .margin({ bottom: 16 })
            .width('100%')

          // ---------- 密码输入框 ----------
          TextInput({ placeholder: '请输入密码' })
            .placeholderColor('#999999')
            .placeholderFont({ size: 16 })
            .type(InputType.Password)
            .textAlign(TextAlign.Start)
            .caretColor('#007DFF')
            .onChange((value: string) => {
              this.password = value;
            })
            .border({ width: 1, color: '#E5E5E5', radius: 15 })
            .padding(8)
            .margin({ bottom: 20 })
            .width('100%')
        }

        // ---------- 登录/注册按钮区域 ----------
        Row() {
          Button(this.isLogin ? '登录' : '注册')
            .type(ButtonType.Capsule)
            .backgroundColor(this.canLogin() ? '#007DFF' : '#BBDEFB')
            .fontColor(Color.White)
            .borderRadius(20)
            .padding({
              left: 16,
              right: 16,
              top: 8,
              bottom: 8
            })
            .margin(4)
            .width('45%')
            .height(60)
            .enabled(this.canLogin())
            .onClick(() => {
              this.handleLoginOrRegister();
            })

          Button(this.isLogin ? '注册' : '登录')
            .type(ButtonType.Capsule)
            .backgroundColor(this.isLogin ? '#F1F3F5' : '#007DFF')
            .fontColor(this.isLogin ? '#182431' : Color.White)
            .borderRadius(20)
            .padding({
              left: 16,
              right: 16,
              top: 8,
              bottom: 8
            })
            .margin(4)
            .width('45%')
            .height(60)
            .onClick(() => {
              this.isLogin = !this.isLogin; // 确保这行没有多余的console或其他错误
            }) // 确保onClick的回调大括号正确闭合
        }
        .justifyContent(FlexAlign.SpaceAround)
        .width('100%')
        .margin({ bottom: 20 })

        // ---------- 隐私政策同意 ----------
        Row() {
          Checkbox({ name: 'policy', group: 'agreement' })
            .select(this.isAgreePolicy)
            .onChange((value: boolean) => {
              this.isAgreePolicy = value;
            })
            .size({ width: 20, height: 20 })

          Text('登录即表示同意')
            .fontSize(12)
            .fontColor('#666666')
            .margin({ left: 8 })

          Text('《隐私政策》')
            .fontSize(12)
            .fontColor('#007DFF')
            .onClick(() => {
              this.showPolicyDialog('隐私政策');
            })

          Text('与')
            .fontSize(12)
            .fontColor('#666666')
            .margin({ left: 2 })

          Text('《用户协议》')
            .fontSize(12)
            .fontColor('#007DFF')
            .onClick(() => {
              this.showPolicyDialog('用户协议');
            })
        }
        .width('100%')
        .justifyContent(FlexAlign.Center)
        .margin({ bottom: 40 })
      }
      .width('90%')
      .margin({ top: 28 })
    }
    .width('100%')
    .height('100%')
    .padding(16)
    .backgroundColor(Color.White)
  }

  // 检查是否可以登录
  private canLogin(): boolean {
    return this.account.length > 0 && this.password.length > 0 && this.isAgreePolicy;
  }

  // 处理登录/注册
  private handleLoginOrRegister(): void {
    if (this.isLogin) {
      // 验证输入
      if (!this.account || !this.password) {
        this.showToast('请输入账号和密码');
        return;
      }

      // 根据身份跳转到不同页面
      if (this.identity === '子女') {
        router.replaceUrl({
          url: 'pages/HomePage',
          params: {
            identity: this.identity,
            account: this.account
          }
        });
      } else if (this.identity === '机构/医生') {
        router.replaceUrl({
          url: 'pages/DoctorHomePage',
          params: {
            identity: this.identity,
            account: this.account
          }
        });
      } else {
        this.showToast('请选择身份');
      }
    } else {
      // 注册逻辑（简化版）
      if (!this.account || !this.password) {
        this.showToast('请输入账号和密码');
        return;
      }

      this.isLogin = true; // 注册成功后切换到登录模式
      this.showToast('注册成功，请登录');
    }
  }

  // 显示协议对话框
  private showPolicyDialog(title: string): void {
    // 这里可以跳转到协议页面或显示自定义弹窗
    this.showToast(`请阅读并同意${title}`);
  }

  // 显示Toast提示
  private showToast(message: string): void {
    // 实际项目中可以使用官方的PromptAction.showToast
    console.log('Toast:', message);
    // 示例：使用自定义Toast组件
    // this.toast = message;
  }
}
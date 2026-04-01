use anchor_lang::prelude::*;

declare_id!("EdrjHLN9K9eogJ5Pui8WYJRAghdN4knAdAoDcZesAirc");

#[program]
pub mod protoqol_core {
    use super::*;

    /// Главная и единственная инструкция протокола для Хакатона.
    /// Сохраняет финальный результат аудита ИИ в блокчейн.
    pub fn etch_deed(
        ctx: Context<EtchDeed>,
        deed_id: String,
        integrity_hash: String,
        impact_score: u8,
        verdict: String,
    ) -> Result<()> {
        let registry = &mut ctx.accounts.deed_record;
        registry.deed_id = deed_id;
        registry.integrity_hash = integrity_hash;
        registry.impact_score = impact_score;
        registry.verdict = verdict;
        registry.timestamp = Clock::get()?.unix_timestamp;
        registry.authority = ctx.accounts.authority.key();

        msg!("ProtoQol Integrity Etched: {} | Verdict: {} | Score: {}", 
            registry.deed_id, registry.verdict, impact_score);
        Ok(())
    }
}

#[derive(Accounts)]
#[instruction(deed_id: String)]
pub struct EtchDeed<'info> {
    #[account(
        init,
        payer = authority,
        space = 8 + DeedRecord::INIT_SPACE,
        seeds = [b"deed", deed_id.as_bytes()],
        bump
    )]
    pub deed_record: Account<'info, DeedRecord>,
    
    #[account(mut)]
    pub authority: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[account]
#[derive(InitSpace)]
pub struct DeedRecord {
    #[max_len(36)]
    pub deed_id: String,      // UUID отчета
    #[max_len(64)]
    pub integrity_hash: String, // SHA-256 хеш данных
    pub impact_score: u8,      // 0-100 оценка ИИ
    #[max_len(8)]
    pub verdict: String,      // "ADAL" или "ARAM"
    pub timestamp: i64,       // Время записи
    pub authority: Pubkey,    // Кто подписал (Master Authority)
}

